from django.db import models


class Author(models.Model):
    first_name = models.CharField(max_length=100, help_text="First name")
    last_name = models.CharField(max_length=100, help_text="Last name")
    date_of_birth = models.DateField(help_text="Date of birth")
    date_of_death = models.DateField(help_text="Date of death", null=True)

    class Meta:
        db_table = "gql_author"


class Publisher(models.Model):
    name = models.CharField(max_length=255, help_text="Name")
    address = models.TextField(help_text="Address")

    class Meta:
        db_table = "gql_publisher"


class Genre(models.Model):
    name = models.CharField(max_length=100, help_text="Name")

    class Meta:
        db_table = "gql_genre"


class Book(models.Model):
    title = models.CharField(max_length=255, help_text="Title")
    summary = models.TextField(help_text="Summary")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books", help_text="Author")
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        related_name="books",
        null=True,
        help_text="Publisher",
    )
    genre = models.ManyToManyField(Genre, related_name="books", help_text="Genre")
    publish_date = models.DateField(help_text="Publish date")

    class Meta:
        db_table = "gql_book"
