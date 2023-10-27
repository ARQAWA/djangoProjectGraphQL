from django.urls import path

from djangoProject.services.strawberry_schema_generator import AsyncAutoGraphQLView

urlpatterns = [
    path("graphql/", AsyncAutoGraphQLView.as_view()),
]
