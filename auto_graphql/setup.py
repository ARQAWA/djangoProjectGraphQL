import importlib
from typing import cast

from django.conf import settings
from django.urls import (
    URLPattern,
    path,
)

from .mapper import AsyncAutoGraphQLView


def setup_global_endpoint() -> None:
    """Setup global endpoint for GraphQL."""

    try:
        urls_py = importlib.import_module(settings.ROOT_URLCONF)
    except ImportError:
        raise RuntimeError("Could not import ROOT_URLCONF.")

    urlpatterns = cast(list[URLPattern], getattr(urls_py, "urlpatterns", None))
    if urlpatterns is None:
        raise ValueError("ROOT_URLCONF must define urlpatterns in order to setup global endpoint.")

    route_path = getattr(settings, "AUTOGRAPHQL_GLOBAL_ROUTE", "auto-graphql-generated")
    if not isinstance(route_path, str):
        raise ValueError("AUTOGRAPHQL_GLOBAL_ROUTE setting must be a string.")

    urlpatterns.append(path(route_path, AsyncAutoGraphQLView.as_view()))
