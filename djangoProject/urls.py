from django.urls import path

from djangoProject.services.graphql_query_scanner import AsyncAutoGraphQLView

urlpatterns = [
    path("graphql/", AsyncAutoGraphQLView.as_view()),
]
