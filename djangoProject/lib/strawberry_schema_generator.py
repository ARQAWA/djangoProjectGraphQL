# import copy
# from collections import deque
# from enum import Enum
# from typing import (
#     Any,
#     Callable,
#     cast,
# )
#
# import inflection
# import strawberry
# import strawberry.django
# from django.apps import apps
# from django.db.models import (
#     Field,
#     ManyToManyField,
#     Model,
# )
# from django.db.models.options import Options
# from django.http import HttpResponse
# from strawberry.django.views import AsyncGraphQLView
# from strawberry_django.optimizer import DjangoOptimizerExtension
#
# __all__ = ("AsyncAutoGraphQLView",)
#
# ModelPath, AppName, AppModelName, FieldName, IsManyRelation = str, str, str, str, bool
# RelationFieldSetterArgs = tuple[AppModelName, Field, type[Model]]  # type: ignore
#
#
# class Mapper:
#     """Django models to strawberry types mapper"""
#
#     class Types(Enum):
#         """Enum for mapping types"""
#
#         Types = "Types"
#         Filters = "Filters"
#         Orders = "Orders"
#
#     def __init__(self, map_type: Types):
#         self._map_type = map_type
#
#         # apps names
#         self._apps_names_unique: set[AppName] = set()
#         self._app_name_by_app_config_names: dict[str, AppName] = {}
#
#         # app models names
#         self._model_names_unique: set[AppModelName] = set()
#         self._model_names_by_model_paths: dict[ModelPath, AppModelName] = {}
#
#         # scheme type dicts
#         self._models_by_model_names: dict[AppModelName, type[Model]] = {}
#         self._types_by_model_names: dict[AppModelName, type] = {}
#         self._plain_types_by_model_names: dict[AppModelName, type] = {}
#         self._relations_setter_queue: deque[RelationFieldSetterArgs] = deque()
#         self._strawberry_plain_types_by_model_names: dict[AppModelName, type] = {}
#
#     @property
#     def map(self) -> dict[AppModelName, type]:
#         return self._types_by_model_names
#
#     @staticmethod
#     def _claim_unique_str(str_base: str, uniques: set[str]) -> str:
#         """Claim unique string by adding number to base string"""
#
#         count = 0
#         result = str_base
#         while True:
#             if result not in uniques:
#                 return result
#             count += 1
#             result = f"{str_base}{count}"
#
#     @staticmethod
#     def _get_meta(model: type[Model]) -> Options:
#         return cast(Options, getattr(model, "_meta"))  # type: ignore
#
#     def _claim_app_name(self, model: type[Model]) -> AppName:
#         """
#         Claim unique name for app
#
#         :param model: Django model type
#         :return: app name
#         """
#
#         model_meta = self._get_meta(model)
#
#         app_name = self._app_name_by_app_config_names.get(model_meta.app_config.name)
#         if app_name is None:
#             app_name = self._claim_unique_str(inflection.camelize(model_meta.app_config.name), self._apps_names_unique)
#             self._apps_names_unique.add(app_name)
#             self._app_name_by_app_config_names[model_meta.app_config.name] = app_name
#
#         return app_name
#
#     def _claim_model_name(self, model: type[Model]) -> AppModelName:
#         """
#         Claim unique name camel cased for model
#
#         :param model: Django model type
#         :return: model name camel cased
#         """
#
#         model_meta = self._get_meta(model)
#
#         object_name = cast(str, model_meta.object_name)
#         model_path = f"{model_meta.app_config.name}.{object_name}"
#
#         model_name = self._model_names_by_model_paths.get(model_path)
#         if model_name is None:
#             model_name = self._claim_unique_str(
#                 inflection.camelize(f"{self._claim_app_name(model)}{object_name}"),
#                 self._model_names_unique,
#             )
#             self._model_names_unique.add(model_name)
#             self._model_names_by_model_paths[model_path] = model_name
#
#         return model_name
#
#     def _put_relation_field(self, model: type[Model], field: Field) -> None:
#         """Put relation field to queue"""
#
#         related_model = cast(type[Model], field.related_model)
#         self._relations_setter_queue.append((self._claim_model_name(model), field, related_model))
#
#         related_model_name = self._claim_model_name(related_model)
#         remote_field = cast(Field, field.remote_field)
#         self._relations_setter_queue.append((related_model_name, remote_field, model))
#
#     def _apply_fields_relations(self) -> None:
#         """Register relations fields"""
#
#         while len(self._relations_setter_queue):
#             model_name, field, related_model = self._relations_setter_queue.popleft()
#
#             self._set_type_to_map(related_model)
#             related_model_name = self._claim_model_name(related_model)
#
#             field_name = field.name
#             field_type = self._get_plain_strawberry_type(related_model_name)
#
#             if field.one_to_many or field.many_to_many:
#                 field_type = list[field_type]
#
#             mapped_type = self._types_by_model_names[model_name]
#             mapped_type.__annotations__[field_name] = field_type
#
#     def _get_plain_strawberry_type(self, model_name: AppModelName) -> type:
#         """
#         Get plain strawberry type
#
#         :param model_name: model name
#         :return: plain strawberry type
#         """
#
#         strawberry_plain_type = self._strawberry_plain_types_by_model_names.get(model_name)
#         if strawberry_plain_type is None:
#             strawberry_plain_type = copy.deepcopy(self._plain_types_by_model_names[model_name])
#             self._apply_strawberry_decorator(model_name, strawberry_plain_type)
#             self._strawberry_plain_types_by_model_names[model_name] = strawberry_plain_type
#
#         return strawberry_plain_type
#
#     def _apply_strawberry_decorator(self, model_name: AppModelName, model_type) -> None:
#         """
#         Apply strawberry decorator
#
#         :param model_name: model name
#         :param model_type: model type
#         """
#
#         name = model_type.__name__
#         model = self._models_by_model_names[model_name]
#         match self._map_type:
#             case self._map_type.Orders:
#                 strawberry.django.order(model, name=name)(model_type)
#             case self._map_type.Filters:
#                 strawberry.django.filter(model, name=name, lookups=True)(model_type)
#             case self._map_type.Types:
#                 strawberry.django.type(model, name=name, pagination=True)(model_type)
#
#     def _set_type_to_map(self, model: type[Model]) -> None:
#         """
#         Set field dict for model
#
#         :param model: Django model type
#         """
#
#         model_name = self._claim_model_name(model)
#
#         if model_name in self._types_by_model_names:
#             return
#
#         self._models_by_model_names[model_name] = model
#
#         model_meta = self._get_meta(model)
#
#         field_dict: dict[FieldName, Any] = {}
#         for field in model_meta.fields:  # type: Field
#             if not field.hidden:
#                 field_dict[field.name] = strawberry.auto
#                 if field.is_relation and not field.one_to_one:
#                     self._put_relation_field(model, field)
#
#         for mm_field in model_meta.many_to_many:  # type: ManyToManyField
#             self._put_relation_field(model, mm_field)
#
#         model_type_name = f"{model_name}{str(self._map_type.value)}"
#         self._types_by_model_names[model_name] = type(model_type_name, (), {"__annotations__": field_dict})
#
#         model_plain_type_name = f"{model_name}{str(self._map_type.value)}Plain"
#         self._plain_types_by_model_names[model_name] = type(model_plain_type_name, (), {"__annotations__": field_dict})
#
#     def register_types_from_models(self, models: list[type[Model]]) -> "Mapper":
#         """
#         Register models dicts
#
#         :param models: Django models types
#         :return: self
#         """
#
#         for model in models:
#             self._set_type_to_map(model)
#         self._apply_fields_relations()
#
#         for model_name, model_type in self._types_by_model_names.items():
#             self._apply_strawberry_decorator(model_name, model_type)
#
#         return self
#
#
# class AsyncAutoGraphQLView:
#     """Class for automatic GraphQL schema generation based on Django models"""
#
#     @classmethod
#     def as_view(cls) -> Callable[..., HttpResponse]:
#         """Generate GraphQL view based on Django models, exclude django.contrib"""
#
#         app_models: list[type[Model]] = []
#         for app_config in apps.get_app_configs():
#             if app_config.name.startswith("django.contrib"):
#                 continue
#
#             app_models.extend(app_config.get_models())
#
#         filters = Mapper(Mapper.Types.Filters).register_types_from_models(app_models).map
#         orders = Mapper(Mapper.Types.Orders).register_types_from_models(app_models).map
#         types = Mapper(Mapper.Types.Types).register_types_from_models(app_models).map
#
#         # generate query
#         type_dict = {
#             type_name: strawberry.django.field(
#                 graphql_type=list[types[type_name]],
#                 filters=filters[type_name],
#                 order=orders[type_name],
#             )  # type: ignore
#             for type_name in types
#         }
#
#         return AsyncGraphQLView.as_view(
#             schema=strawberry.Schema(
#                 query=strawberry.type()(type("AutoGeneratedQuery", (), type_dict)),
#                 extensions=[DjangoOptimizerExtension],
#             )
#         )
