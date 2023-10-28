from django.urls import path

from djangoProject.lib.django_model_mapper import AsyncAutoGraphQLView

urlpatterns = [
    path("graphql/", AsyncAutoGraphQLView.as_view()),
]
