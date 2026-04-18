from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True, related_name="posts"
    )
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.title
