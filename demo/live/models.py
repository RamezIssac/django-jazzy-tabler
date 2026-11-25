from django.db import models


class DemoReset(models.Model):
    """Single row (pk=1) holding when the demo data was last reset; its row lock serialises resets."""

    reset_at = models.DateTimeField(null=True, blank=True)
