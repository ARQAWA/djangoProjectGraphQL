from django.db import models


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    date_of_death = models.DateField(null=True)


class Publisher(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()


class Genre(models.Model):
    name = models.CharField(max_length=100)


class Book(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, related_name="books", null=True)
    genres = models.ManyToManyField(Genre, related_name="books")
    publish_date = models.DateField()
