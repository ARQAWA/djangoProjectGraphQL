from django.apps import AppConfig

from .setup import setup_global_endpoint


class AutoGraphqlConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auto_graphql"

    def ready(self) -> None:
        setup_global_endpoint()
