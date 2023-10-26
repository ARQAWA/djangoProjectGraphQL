from enum import Enum
from typing import (
    Any,
    List,
    cast,
)

import inflection
import strawberry
import strawberry.django
from django.db.models import (
    ManyToManyField,
    Model,
)
from django.db.models.options import Options


class MapperEnum(Enum):
    """Enum for mapping types"""

    Types = "Types"
    Filters = "Filters"
    Orders = "Orders"


class StrawberryModelMapper:
    """Mapper for Django models to strawberry types"""

    _apps_names_camel_names: dict[str, str] = {}
    _apps_camel_names_unique: set[str] = set()
    _apps_models_names: dict[str, str] = {}
    _apps_models_backrefs: dict[str, tuple[str, Model]] = {}

    @classmethod
    def _set_backrefs(cls, model: type[Model]) -> None:
        """
        Set backrefs for model

        Args:
            model: Django model
        """

        model_meta = cast(Options, getattr(model, "_meta"))

    @classmethod
    def _regisetr_app_name_camel(cls, app_name: str) -> None:
        """
        Register app name camel cased

        Args:
            app_name: name of the app
        """

        if app_name in cls._apps_names_camel_names:
            return

        app_name_camel = inflection.camelize(app_name)
        if app_name_camel in cls._apps_camel_names_unique:
            app_name_camel += "1"

        cls._apps_camel_names_unique.add(app_name_camel)
        cls._apps_names_camel_names[app_name] = app_name_camel

    @classmethod
    def _get_app_model_name_camel(cls, model: type[Model]) -> str:
        """
        Get app model name camel cased by app name and model name

        Args:
            model: Django model

        Returns:
            camel cased app model name
        """

        model_meta = cast(Options, getattr(model, "_meta"))  # type: ignore

        app_model_key = f"{model_meta.app_config.name}.{model_meta.object_name}"
        app_model_name_camel = cls._apps_models_names.get(app_model_key, None)
        if app_model_name_camel is None:
            # get app name camel cased
            app_name = model_meta.app_config.name
            app_name_camel = cls._apps_names_camel_names.get(app_name, None)
            if app_name_camel is None:
                cls._regisetr_app_name_camel(app_name)
            app_name_camel = cls._apps_names_camel_names[app_name]

            # register app model name camel cased
            camelized_object_name = inflection.camelize(str(model_meta.object_name))
            app_model_name_camel = f"{app_name_camel}{camelized_object_name}"
            cls._apps_models_names[app_model_key] = app_model_name_camel

        return app_model_name_camel

    @classmethod
    def _get_map_class(cls, mapping_type: MapperEnum) -> type:
        """
        Get map class for mapping type

        Args:
            mapping_type: type of mapping
        Returns:
            map class
        """
        map_class = getattr(cls, mapping_type.value, None)

        if map_class is None:
            map_class = type(mapping_type.value, (), {})
            setattr(cls, mapping_type.value, map_class)

        return map_class

    @classmethod
    def set_strawberry_type(
        cls,
        model: type[Model],
        mapping_type: MapperEnum,
    ) -> None:
        """
        Set model for mapping

        Args:
            model: Django model
            mapping_type: type of mapping
        """

        app_model_name_camel = cls._get_app_model_name_camel(model)
        model_meta = cast(Options, getattr(model, "_meta"))  # type: ignore

        map_class = cls._get_map_class(mapping_type)
        if hasattr(map_class, app_model_name_camel):
            return

        fields: dict[str, Any] = {}
        for field in model_meta.fields:
            if not field.hidden:
                field_type = strawberry.auto
                if field.is_relation:
                    related_model = cast(type[Model], field.related_model)
                    cls.set_strawberry_type(related_model, mapping_type)
                    field_type = getattr(map_class, cls._get_app_model_name_camel(related_model))
                fields[field.name] = field_type

        if many_to_many := cast(tuple[ManyToManyField], getattr(model_meta, "many_to_many")):  # type: ignore
            for many_to_many_field in many_to_many:
                related_model = cast(type[Model], many_to_many_field.related_model)
                cls.set_strawberry_type(related_model, mapping_type)
                mm_field_type = getattr(map_class, cls._get_app_model_name_camel(related_model))
                fields[many_to_many_field.name] = List[mm_field_type]  # type: ignore

        strawberry_obj_name = f"{app_model_name_camel}{mapping_type.value}"
        strawberry_obj_class = type(strawberry_obj_name, (), {"__annotations__": fields})

        match mapping_type:
            case mapping_type.Orders:
                strawberry_decorator = strawberry.django.order(model, name=strawberry_obj_name)
            case mapping_type.Filters:
                strawberry_decorator = strawberry.django.filter(model, name=strawberry_obj_name, lookups=True)
            case mapping_type.Types:
                orders = getattr(cls._get_map_class(mapping_type.Orders), app_model_name_camel)
                filters = getattr(cls._get_map_class(mapping_type.Filters), app_model_name_camel)
                strawberry_decorator = strawberry.django.type(
                    model,
                    name=strawberry_obj_name,
                    filters=filters,
                    order=orders,
                    pagination=True,
                )
            case _:
                raise ValueError(f"Unknown mapping type: {mapping_type.value}")

        setattr(map_class, app_model_name_camel, strawberry_decorator(strawberry_obj_class))

    @classmethod
    def get_graphql_types(cls) -> dict[str, type]:
        """
        Get strawberry models types by their names camel cased

        Returns:
            dictionary of strawberry models types
        """

        map_class = cls._get_map_class(MapperEnum.Types)

        result: dict[str, type] = {}
        for app_model_name_camel in cls._apps_models_names.values():
            result[app_model_name_camel] = cast(type, getattr(map_class, app_model_name_camel))

        return result
