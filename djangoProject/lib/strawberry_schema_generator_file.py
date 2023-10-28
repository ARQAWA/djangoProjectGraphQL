# import os
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
# RelationFieldSetterArgs = tuple[AppModelName, Field, type[Model]]
#
#
# class Mapper:
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
#         self._types_by_model_names: dict[AppModelName, type] = {}
#         self._models_by_model_names: dict[AppModelName, type[Model]] = {}
#         self._types_str_by_model_names: dict[AppModelName, str] = {}
#         self._relations_setter_queue: deque[RelationFieldSetterArgs] = deque()
#
#         # text blocks
#         self._class_text_blocks: dict[AppModelName, str] = {}
#
#     @property
#     def types_map(self) -> dict[AppModelName, type]:
#         return self._types_by_model_names
#
#     @property
#     def models_map(self) -> dict[AppModelName, type[Model]]:
#         return self._models_by_model_names
#
#     @property
#     def class_text_map(self) -> dict[AppModelName, str]:
#         return self._class_text_blocks
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
#     def _claim_app_name(self, model: type[Model]) -> AppName:
#         """
#         Claim unique name for app
#
#         :param model: Django model type
#         :return: app name
#         """
#
#         model_meta = _get_meta(model)
#
#         app_name = self._app_name_by_app_config_names.get(model_meta.app_config.name)
#         if app_name is None:
#             app_name = self._claim_unique_str(inflection.camelize(model_meta.app_config.name), self._apps_names_unique)
#             self._apps_names_unique.add(app_name)
#             self._app_name_by_app_config_names[model_meta.app_config.name] = app_name
#
#         return app_name
#
#     def _claim_model_name(
#         self,
#         model: type[Model],
#     ) -> AppModelName:
#         """
#         Claim unique name camel cased for model
#
#         :param model: Django model type
#         :return: model name camel cased
#         """
#
#         model_meta = _get_meta(model)
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
#     def _put_relation_field(
#         self,
#         model: type[Model],
#         field: Field,
#     ) -> None:
#         """Put relation field to queue"""
#
#         related_model = cast(type[Model], field.related_model)
#         self._relations_setter_queue.append((self._claim_model_name(model), field, related_model))
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
#             field_type = self._types_by_model_names[related_model_name]
#
#             if field.one_to_many or field.many_to_many:
#                 field_type = f'"list[{field_type.__name__}]"'
#             else:
#                 field_type = f'"{field_type.__name__}"'
#
#             mapped_type = self._types_by_model_names[model_name]
#             mapped_type.__annotations__[field_name] = field_type
#
#     def _apply_strawberry_decorators(self):
#         """Apply strawberry decorators to types"""
#
#         for model_name, model_type in self._types_by_model_names.items():
#             match self._map_type:
#                 case self.Types.Orders:
#                     class_text_block = f"@strawberry.django.order(DjangoModel{model_name})\n"
#                 case self.Types.Filters:
#                     class_text_block = f"@strawberry.django.filter(DjangoModel{model_name}, lookups=True)\n"
#                 case self.Types.Types:
#                     class_text_block = f"@strawberry.django.type(DjangoModel{model_name})\n"
#                 case _:
#                     raise NotImplementedError
#
#             class_text_block += f"class {model_type.__name__}:\n"
#             for field_name, field_type in model_type.__annotations__.items():
#                 class_text_block += f"    {field_name}: {field_type}\n"
#             class_text_block += "\n\n"
#
#             self._class_text_blocks[model_name] = class_text_block
#
#     #
#     # def _apply_strawberry_decorators(self):
#     #     """Apply strawberry decorators to types"""
#     #
#     #     for model_name, model_type in self._types_by_model_names.items():
#     #         pprint.pp(model_type)
#     #         name = model_type.__name__
#     #         model = self._models_by_model_names[model_name]
#     #         match self._map_type:
#     #             case self.Types.Orders:
#     #                 strawberry.django.order(model, name=name)(model_type)
#     #             case self.Types.Filters:
#     #                 strawberry.django.filter(model, name=name, lookups=True)(model_type)
#     #             case self.Types.Types:
#     #                 strawberry.django.type(model, name=name)(model_type)
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
#         model_meta = _get_meta(model)
#
#         field_dict: dict[FieldName, Any] = {}
#         for field in model_meta.fields:  # type: Field
#             if not field.hidden:
#                 field_dict[field.name] = "auto"
#                 if field.is_relation:
#                     self._put_relation_field(model, field)
#
#         for mm_field in model_meta.many_to_many:  # type: ManyToManyField
#             self._put_relation_field(model, mm_field)
#
#         type_name = f"{model_name}{str(self._map_type.value)}"
#         type_obj = type(type_name, (), {"__annotations__": field_dict})
#         self._types_by_model_names[model_name] = type_obj
#         self._models_by_model_names[model_name] = model
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
#         self._apply_strawberry_decorators()
#
#         return self
#
#
# class AsyncAutoGraphQLView:
#     """Class for automatic GraphQL schema generation based on Django models"""
#
#     @staticmethod
#     def _write_module_file(mappers: tuple[Mapper, Mapper, Mapper]) -> str:
#         genered_module_name = "generated_graphql_strawberry_types_schema"
#
#         filters, orders, types = mappers
#
#         # save text to root directory
#         with open(f"./{genered_module_name}.py", "w") as f:
#             f.write("import strawberry.django\n" "from strawberry import auto\n")
#             for type_name, model in types.models_map.items():
#                 model_meta = _get_meta(model)
#                 model_app = model_meta.app_config.name
#                 f.write(f"from {model_app}.models import {model.__name__} as DjangoModel{type_name}\n")
#             f.write("\n\n")
#
#             for type_map in (filters, orders, types):
#                 for type_name in type_map.class_text_map:
#                     f.write(type_map.class_text_map[type_name])
#
#             f.write("@strawberry.type\n" "class AutogeneratedQuery:\n")
#
#             for type_name in types.types_map:
#                 f.write(
#                     f"    {type_name} = strawberry.django.field("
#                     f"graphql_type=list[{types.types_map[type_name].__name__}], "
#                     f"filters={filters.types_map[type_name].__name__}, "
#                     f"order={orders.types_map[type_name].__name__}, "
#                     f"pagination=True"
#                     f")\n"
#                 )
#
#         # # generate query
#         # type_dict = {
#         #     type_name: strawberry.django.field(
#         #         graphql_type=list[types[type_name]],
#         #         filters=filters[type_name],
#         #         order=orders[type_name],
#         #         pagination=True,
#         #     )  # type: ignore
#         #     for type_name in types
#         # }
#
#         return genered_module_name
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
#         filters = Mapper(Mapper.Types.Filters).register_types_from_models(app_models)
#         orders = Mapper(Mapper.Types.Orders).register_types_from_models(app_models)
#         types = Mapper(Mapper.Types.Types).register_types_from_models(app_models)
#
#         # write module file
#         genered_module_name = cls._write_module_file((filters, orders, types))
#
#         import importlib
#
#         query_generated = getattr(importlib.import_module(genered_module_name), "AutogeneratedQuery")
#
#         exit()
#
#         os.remove(f"./{genered_module_name}.py")
#
#         return AsyncGraphQLView.as_view(
#             schema=strawberry.Schema(
#                 query=query_generated,
#                 extensions=[DjangoOptimizerExtension],
#             )
#         )
#
#
# def _get_meta(model: type[Model]) -> Options:
#     return cast(Options, getattr(model, "_meta"))  # type: ignore
