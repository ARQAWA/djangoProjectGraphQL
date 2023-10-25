from django.apps import apps


class GraphQLQueryFabric:
    """This class is responsible for generating GraphQL queries from Django models"""

    def __init__(self) -> None:
        self._apps_and_models = self._construct_apps_and_models()

    @staticmethod
    def _construct_apps_and_models() -> dict[str, set[str]]:
        apps_and_models: dict[str, set[str]] = {}

        for app_config in apps.get_app_configs():
            if app_config.name.startswith("django.contrib"):
                continue

            model_names = set()
            for model in app_config.get_models():
                model_name = getattr(getattr(model, "_meta"), "object_name")
                model_names.add(model_name)

            print(app_config.name, model_names)
            apps_and_models[app_config.name] = model_names

        return apps_and_models
