# Generated by Django 4.2.6 on 2023-10-24 21:20
from typing import cast

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

from zorgs import models as zorgs_models


# noinspection PyPep8Naming
def create_data(apps: StateApps, _schema_editor: BaseDatabaseSchemaEditor) -> None:
    MegaZorg = cast(type[zorgs_models.MegaZorg], apps.get_model("zorgs", "MegaZorg"))

    MegaZorg.objects.bulk_create([MegaZorg(name=f"Zorg #{i}") for i in range(1, 101)])


class Migration(migrations.Migration):
    dependencies = [
        ("zorgs", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_data, migrations.RunPython.noop)]
