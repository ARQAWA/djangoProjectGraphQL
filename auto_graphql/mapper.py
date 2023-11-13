import copy
from collections import deque
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    Type,
    cast,
)

import inflection
import strawberry
from django.apps import apps
from django.db.models import (
    Field,
    Model,
)
from django.db.models.options import Options
from strawberry.django.views import AsyncGraphQLView
from strawberry_django.optimizer import DjangoOptimizerExtension

# type aliases
AppName = Annotated[str, "AppName"]
AppModelName = Annotated[str, "AppModelName"]
ModelPath = Annotated[str, "ModelPath"]
FieldName = Annotated[str, "FieldName"]
DjangoModel = Annotated[Type[Model], "DjangoModel"]
TypeObj = Annotated[Any, "TypeObj"]
RelationFieldSetterArgs = tuple[AppModelName, Field, TypeObj]  # type: ignore


class Mapper:
    def __init__(self) -> None:
        self.types: Dict[AppModelName, TypeObj] = {}
        self._models: Dict[AppModelName, DjangoModel] = {}
        self._orders: Dict[AppModelName, TypeObj] = {}
        self._filters: Dict[AppModelName, TypeObj] = {}
        self._apps_names: Dict[str, AppName] = {}
        self._model_names: Dict[ModelPath, AppModelName] = {}
        self._unique_app_names: set[str] = set()
        self._unique_model_names: set[str] = set()
        self._relations_queue: deque[RelationFieldSetterArgs] = deque()

    @staticmethod
    def _claim_unique_str(str_base: str, uniques: set[str]) -> str:
        """Claim unique string by adding number to base string"""

        count = 0
        result = str_base
        while True:
            if result not in uniques:
                uniques.add(result)
                return result
            count += 1
            result = f"{str_base}{count}"

    @staticmethod
    def _get_meta(model: DjangoModel) -> Options:  # type: ignore
        return cast(Options, getattr(model, "_meta"))  # type: ignore

    def _register_app_name(self, model: DjangoModel) -> AppName:
        app_config_name = self._get_meta(model).app_config.name
        app_name = self._apps_names.get(app_config_name)
        if app_name is None:
            app_name = self._apps_names[app_config_name] = self._claim_unique_str(
                inflection.camelize(app_config_name),
                self._unique_app_names,
            )
        return app_name

    def _register_model_name(self, model: DjangoModel) -> AppModelName:
        app_config_name = self._get_meta(model).app_config.name
        model_object_name = cast(str, self._get_meta(model).object_name)
        model_path = f"{app_config_name}.{model_object_name}"
        model_name = self._model_names.get(model_path)
        if model_name is None:
            model_name = self._model_names[model_path] = self._claim_unique_str(
                f"{self._register_app_name(model)}{inflection.camelize(model_object_name)}", self._unique_model_names
            )
        return model_name

    def _enqueue_relation(
        self,
        model: DjangoModel,
        field: Field,  # type: ignore
    ) -> None:
        related_model = cast(TypeObj, field.related_model)
        self._relations_queue.append((self._register_model_name(model), field, related_model))

        related_model_name = self._register_model_name(related_model)
        remote_field = cast(Field, field.remote_field)  # type: ignore
        self._relations_queue.append((related_model_name, remote_field, model))

    def _process_relations(self) -> None:
        while self._relations_queue:
            model_name, field, related_model = self._relations_queue.popleft()
            related_model_name = self._register_model_name(related_model)

            field_type = self.types[related_model_name]

            if field.one_to_many or field.many_to_many:
                field_type = cast(Any, List[field_type])  # type: ignore

            setattr(
                self.types[model_name],
                field.name,
                strawberry.field(name=related_model_name, graphql_type=field_type),
            )

    def _create_type(self, model: DjangoModel) -> None:
        model_name = self._register_model_name(model)
        self._models[model_name] = model

        fields_dict: Dict[FieldName, Any] = {}
        for field in self._get_meta(model).fields:
            if field.hidden:
                continue
            elif field.is_relation:
                self._enqueue_relation(model, field)
            else:
                fields_dict[field.name] = strawberry.auto

        for mm_field in self._get_meta(model).many_to_many:  # type: ignore
            self._enqueue_relation(model, mm_field)

        object_dict = {"__annotations__": fields_dict}

        self.types[model_name] = type(f"{model_name}Types", (), copy.deepcopy(object_dict))
        self._orders[model_name] = type(f"{model_name}Orders", (), copy.deepcopy(object_dict))
        self._filters[model_name] = type(f"{model_name}Filters", (), copy.deepcopy(object_dict))

    def register_models(self, models: List[DjangoModel]) -> None:
        for model in models:
            self._create_type(model)

        self._process_relations()

        for model_name, type_obj in self.types.items():
            model = self._models[model_name]
            order_obj = self._orders[model_name]
            filter_obj = self._filters[model_name]
            strawberry.django.order(model, name=order_obj.__name__)(order_obj)
            strawberry.django.filter(model, name=filter_obj.__name__, lookups=True)(filter_obj)
            strawberry.django.type(
                model,
                name=type_obj.__name__,
                filters=filter_obj,
                order=order_obj,
                pagination=True,
            )(type_obj)


class AsyncAutoGraphQLView:
    @classmethod
    def as_view(cls) -> Callable[..., Any]:
        app_models = [
            model
            for app_config in apps.get_app_configs()
            if not app_config.name.startswith("django.contrib")
            for model in app_config.get_models()
        ]

        mapper = Mapper()
        mapper.register_models(app_models)

        query_types_dict = {
            type_name: strawberry.django.field(graphql_type=List[type_obj])  # type: ignore
            for type_name, type_obj in mapper.types.items()
        }

        query_object = strawberry.type()(type("AutoGeneratedQueryRecursive", (), query_types_dict))
        del mapper, query_types_dict

        return AsyncGraphQLView.as_view(
            schema=strawberry.Schema(
                query=query_object,
                extensions=[DjangoOptimizerExtension],
            )
        )
