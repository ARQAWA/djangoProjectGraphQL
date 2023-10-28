from django.urls import path

from djangoProject.lib.strawberry_schema_generator_recursive import AsyncAutoGraphQLView

urlpatterns = [
    path("graphql/", AsyncAutoGraphQLView.as_view()),
]
