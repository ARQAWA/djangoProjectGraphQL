# Generated by Django 4.2.6 on 2023-10-24 21:20
import hashlib
import random
from typing import cast

from django.db import (
    migrations,
    transaction,
)
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

from blog import models as blog_models


# noinspection PyPep8Naming
def create_data(apps: StateApps, _schema_editor: BaseDatabaseSchemaEditor) -> None:
    Sign = cast(type[blog_models.Sign], apps.get_model("blog", "Sign"))
    Author = cast(type[blog_models.Author], apps.get_model("blog", "Author"))
    Tag = cast(type[blog_models.Tag], apps.get_model("blog", "Tag"))
    Article = cast(type[blog_models.Article], apps.get_model("blog", "Article"))

    with transaction.atomic():
        signs = [
            Sign(data=hashlib.sha256("Sign One".encode("utf-8")).hexdigest()[:200]),
            Sign(data=hashlib.sha256("Sign Two".encode("utf-8")).hexdigest()[:200]),
            Sign(data=hashlib.sha256("Sign Three".encode("utf-8")).hexdigest()[:200]),
        ]
        Sign.objects.bulk_create(signs)

        authors = [
            Author(name="Author One", bio="Bio One", sign=signs[0]),
            Author(name="Author Two", bio="Bio Two", sign=signs[1]),
            Author(name="Author Three", bio="Bio Three", sign=signs[2]),
        ]
        Author.objects.bulk_create(authors)

        articles = [
            Article(
                title=f"Article #{i}",
                content=f"Content for Article #{i}",
                author=authors[i % 3],
            )
            for i in range(1, 11)
        ]
        Article.objects.bulk_create(articles)

        tags = [Tag(name=f"Tag #{i}", description=f"Description for Tag #{i}") for i in range(1, 21)]
        Tag.objects.bulk_create(tags)

        for tag in Tag.objects.all():
            tag.articles.add(articles[random.randint(0, 9)])


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_data, migrations.RunPython.noop)]
