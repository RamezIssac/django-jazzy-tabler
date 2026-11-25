from django.apps import AppConfig


class LiveDemoConfig(AppConfig):
    name = "demo.live"
    label = "live_demo"
    verbose_name = "Live demo"
    default_auto_field = "django.db.models.BigAutoField"
