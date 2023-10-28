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
#
# __all__ = ("AsyncAutoGraphQLView",)
#
# from strawberry_django.optimizer import DjangoOptimizerExtension
#
# TypeOrder, TypeFilter, TypeObj = type, type, type
# ModelPath, AppName, AppModelName, FieldName = str, str, str, str
# RelationFieldSetterArgs = tuple[AppModelName, Field, type[Model]]  # type: ignore
#
#
# class Mapper:
#     """Django models to strawberry types mapper"""
#
#     def __init__(self):
#         # apps names
#         self._apps_names_unique: set[AppName] = set()
#         self._app_name_by_app_config_names: dict[str, AppName] = {}
#
#         # app models names
#         self._model_names_unique: set[AppModelName] = set()
#         self._model_names_by_model_paths: dict[ModelPath, AppModelName] = {}
#
#         # type object maps
#         self._models_by_model_names: dict[AppModelName, type[Model]] = {}
#         self._relations_setter_queue: deque[RelationFieldSetterArgs] = deque()
#         self._types_by_model_names: dict[AppModelName, TypeObj] = {}
#         self._orders_by_model_names: dict[AppModelName, TypeOrder] = {}
#         self._filters_by_model_names: dict[AppModelName, TypeFilter] = {}
#
#     @property
#     def types_map(self) -> dict[AppModelName, type]:
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
#             related_model_name = self._claim_model_name(related_model)
#
#             field_name = field.name
#             field_type = self._types_by_model_names[related_model_name]
#
#             if field.one_to_many or field.many_to_many:
#                 field_type = list[field_type]
#
#             mapped_type = self._types_by_model_names[model_name]
#             # mapped_type.__annotations__[field_name] = field_type
#
#             setattr(
#                 mapped_type,
#                 field_name,
#                 strawberry.field(name=related_model_name, graphql_type=field_type)
#             )
#
#     def _apply_strawberry_decorators_for_types(self):
#         """Apply strawberry decorators to types"""
#
#         for model_name, type_obj in self._types_by_model_names.items():
#             model = self._models_by_model_names[model_name]
#             order_obj = self._orders_by_model_names[model_name]
#             filter_obj = self._filters_by_model_names[model_name]
#
#             strawberry.django.order(model, name=order_obj.__name__)(order_obj)
#             strawberry.django.filter(model, name=filter_obj.__name__, lookups=True)(filter_obj)
#             strawberry.django.type(
#                 model,
#                 name=type_obj.__name__,
#                 filters=filter_obj,
#                 order=order_obj,
#                 pagination=True,
#             )(type_obj)
#
#     def _set_type_to_map(self, model: type[Model]) -> None:
#         """
#         Set field dict for model
#
#         :param model: Django model type
#         """
#
#         model_name = self._claim_model_name(model)
#         self._models_by_model_names[model_name] = model
#
#         model_meta = self._get_meta(model)
#
#         # prepare field dict for type object annotations
#         field_dict: dict[FieldName, Any] = {}
#         for field in model_meta.fields:  # type: Field
#             if field.hidden:
#                 continue
#             elif field.is_relation:
#                 self._put_relation_field(model, field)
#             else:
#                 field_dict[field.name] = strawberry.auto
#
#         # put many to many fields to queue for later processing
#         for mm_field in model_meta.many_to_many:  # type: ManyToManyField
#             self._put_relation_field(model, mm_field)
#
#         obj_dict = {"__annotations__": field_dict}
#
#         self._types_by_model_names[model_name] = type(f"{model_name}Types", (), copy.deepcopy(obj_dict))
#         self._orders_by_model_names[model_name] = type(f"{model_name}Orders", (), copy.deepcopy(obj_dict))
#         self._filters_by_model_names[model_name] = type(f"{model_name}Filters", (), copy.deepcopy(obj_dict))
#
#     def register_types_from_models(self, models: list[type[Model]]) -> "Mapper":
#         """
#         Register models dicts
#
#         :param models: Django models types
#         """
#
#         for model in models:
#             self._set_type_to_map(model)
#
#         self._apply_fields_relations()
#         self._apply_strawberry_decorators_for_types()
#
#         return self
#
#
# class MapperTypes(Enum):
#     """Enum for mapping types"""
#
#     Types = "Types"
#     Filters = "Filters"
#     Orders = "Orders"
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
#         types_map = Mapper().register_types_from_models(app_models).types_map
#
#         # generate query
#         type_dict = {
#             type_name: strawberry.django.field(graphql_type=list[type_obj])  # type: ignore
#             for type_name, type_obj in types_map.items()
#         }
#
#         return AsyncGraphQLView.as_view(
#             schema=strawberry.Schema(
#                 query=strawberry.type()(type("AutoGeneratedQuery", (), type_dict)),
#                 extensions=[DjangoOptimizerExtension],
#             )
#         )
