from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)


class Tag(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, related_name="articles")
    published_date = models.DateTimeField(auto_now_add=True)
