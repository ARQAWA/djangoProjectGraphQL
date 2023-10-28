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

import strawberry
from django.apps import apps
from django.db.models import (
    Field,
    Model,
)
from django.db.models.options import Options
from strawberry.django.views import AsyncGraphQLView

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
        self.apps_names: Dict[str, AppName] = {}
        self.model_names: Dict[ModelPath, AppModelName] = {}
        self.models: Dict[AppModelName, DjangoModel] = {}
        self.types: Dict[AppModelName, TypeObj] = {}
        self.plains: Dict[AppModelName, TypeObj] = {}
        self.orders: Dict[AppModelName, TypeObj] = {}
        self.filters: Dict[AppModelName, TypeObj] = {}
        self.relations_queue: deque[RelationFieldSetterArgs] = deque()
        self._compiled_types: set[AppModelName] = set()

    @staticmethod
    def _get_meta(model: TypeObj) -> Options:  # type: ignore
        return cast(Options, getattr(model, "_meta"))  # type: ignore

    def _register_app_name(self, model: TypeObj) -> AppName:
        app_config_name = self._get_meta(model).app_config.name
        return self.apps_names.setdefault(app_config_name, app_config_name.replace("_", " ").title().replace(" ", ""))

    def _register_model_name(self, model: TypeObj) -> AppModelName:
        meta = self._get_meta(model)
        model_path = f"{meta.app_config.name}.{meta.object_name}"
        return self.model_names.setdefault(model_path, f"{self._register_app_name(model)}{meta.object_name}")

    def _enqueue_relation(
        self,
        model: TypeObj,
        field: Field,  # type: ignore
    ) -> None:
        related_model = cast(DjangoModel, field.related_model)
        self.relations_queue.append((self._register_model_name(model), field, related_model))

    def _process_relations(self) -> None:
        while self.relations_queue:
            model_name, field, related_model = self.relations_queue.popleft()

            related_model_name = self._register_model_name(related_model)
            related_plain_type = self.plains[related_model_name]
            self._compile_strawberry_type(related_model_name, related_plain_type)

            field_type = related_plain_type
            if field.one_to_many or field.many_to_many:
                field_type = cast(Any, List[field_type])  # type: ignore

            del self.types[model_name].__annotations__[field.name]
            setattr(
                self.types[model_name],
                field.name,
                strawberry.django.field(name=related_model_name, graphql_type=field_type),
            )

    def _create_type(self, model: DjangoModel) -> None:
        model_name = self._register_model_name(model)
        self.models[model_name] = model

        fields_dict: Dict[FieldName, Any] = {}
        for field in self._get_meta(model).fields:
            if not field.hidden:
                fields_dict[field.name] = strawberry.auto
                if field.is_relation:
                    self._enqueue_relation(model, field)

        for mm_field in self._get_meta(model).many_to_many:  # type: ignore
            fields_dict[mm_field.name] = strawberry.auto
            self._enqueue_relation(model, mm_field)

        object_dict = {"__annotations__": fields_dict}

        self.types[model_name] = type(f"{model_name}Types", (), copy.deepcopy(object_dict))
        self.plains[model_name] = type(f"{model_name}Plains", (), copy.deepcopy(object_dict))
        self.orders[model_name] = type(f"{model_name}Orders", (), copy.deepcopy(object_dict))
        self.filters[model_name] = type(f"{model_name}Filters", (), copy.deepcopy(object_dict))

    def _compile_strawberry_type(self, model_name: AppModelName, type_obj: TypeObj) -> None:
        model = self.models[model_name]
        order_obj = self.orders[model_name]
        filter_obj = self.filters[model_name]

        if model_name not in self._compiled_types:
            strawberry.django.order(model, name=order_obj.__name__)(order_obj)
            strawberry.django.filter(model, name=filter_obj.__name__, lookups=True)(filter_obj)
            self._compiled_types.add(model_name)

        strawberry.django.type(
            model,
            name=type_obj.__name__,
            filters=filter_obj,
            order=order_obj,
            pagination=True,
        )(type_obj)

    def register_models(self, models: List[DjangoModel]) -> None:
        for model in models:
            self._create_type(model)

        self._process_relations()

        for model_name, type_obj in self.types.items():
            self._compile_strawberry_type(model_name, type_obj)


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

        query_object = strawberry.type()(type("AutoGeneratedQuery", (), query_types_dict))
        del mapper, query_types_dict

        return AsyncGraphQLView.as_view(
            schema=strawberry.Schema(
                query=query_object,
                # extensions=[DjangoOptimizerExtension],
            )
        )
