import strawberry
from django.contrib import admin
from django.urls import path
from strawberry import auto
from strawberry.django.views import AsyncGraphQLView
from strawberry_django.optimizer import DjangoOptimizerExtension

from zorgs import models as zorgs_models


@strawberry.django.type(zorgs_models.MegaZorg)
class MegaZorgType:
    name: auto
    created_at: auto
    updated_at: auto


@strawberry.type
class Query:
    zorg: MegaZorgType = strawberry.django.field()
    zorgs: list[MegaZorgType] = strawberry.django.field()


schema = strawberry.Schema(
    query=Query,
    extensions=[
        DjangoOptimizerExtension,  # not required, but highly recommended
    ],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", AsyncGraphQLView.as_view(schema=schema)),
]
