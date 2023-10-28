from django.urls import path

from djangoProject.lib.django_model_mapper import AsyncAutoGraphQLView
from djangoProject.lib.django_model_mapper_recursive import AsyncAutoGraphQLView as AsyncAutoGraphQLViewRecursive

urlpatterns = [
    path("graphql/", AsyncAutoGraphQLView.as_view()),
    path("graphql_r/", AsyncAutoGraphQLViewRecursive.as_view()),
]
