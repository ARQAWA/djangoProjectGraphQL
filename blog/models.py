from django.db import models


class Sign(models.Model):
    data = models.CharField(max_length=200, unique=True)


class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    sign = models.OneToOneField(Sign, related_name="author", related_query_name="author", on_delete=models.CASCADE)


class Tag(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    author = models.ForeignKey(Author, related_name="articles", on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, related_name="articles")
    published_date = models.DateTimeField(auto_now_add=True)
