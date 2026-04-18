from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = "demo.blog"
    label = "blog"
    verbose_name = "Blog"
    default_auto_field = "django.db.models.BigAutoField"
