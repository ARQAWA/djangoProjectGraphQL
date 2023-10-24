# Generated by Django 4.2.6 on 2023-10-24 20:43

import django.db.models.deletion
from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Author",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(help_text="First name", max_length=100)),
                ("last_name", models.CharField(help_text="Last name", max_length=100)),
                ("date_of_birth", models.DateField(help_text="Date of birth")),
                ("date_of_death", models.DateField(help_text="Date of death", null=True)),
            ],
            options={
                "db_table": "gql_author",
            },
        ),
        migrations.CreateModel(
            name="Genre",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Name", max_length=100)),
            ],
            options={
                "db_table": "gql_genre",
            },
        ),
        migrations.CreateModel(
            name="Publisher",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Name", max_length=255)),
                ("address", models.TextField(help_text="Address")),
            ],
            options={
                "db_table": "gql_publisher",
            },
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(help_text="Title", max_length=255)),
                ("summary", models.TextField(help_text="Summary")),
                ("publish_date", models.DateField(help_text="Publish date")),
                (
                    "author",
                    models.ForeignKey(
                        help_text="Author",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="books",
                        to="test_django_graphql.author",
                    ),
                ),
                (
                    "genre",
                    models.ManyToManyField(help_text="Genre", related_name="books", to="test_django_graphql.genre"),
                ),
                (
                    "publisher",
                    models.ForeignKey(
                        help_text="Publisher",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="books",
                        to="test_django_graphql.publisher",
                    ),
                ),
            ],
            options={
                "db_table": "gql_book",
            },
        ),
    ]
