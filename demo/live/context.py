from django.conf import settings

from demo.live.turnstile import turnstile_enabled


def last_reset():
    from demo.live.models import DemoReset

    return DemoReset.objects.filter(pk=1).values_list("reset_at", flat=True).first()


def demo_login(request):
    return {
        "demo_username": settings.DEMO_USERNAME,
        "demo_password": settings.DEMO_PASSWORD,
        "demo_reset_hours": settings.DEMO_RESET_HOURS,
        "demo_last_reset": last_reset,
        "turnstile_site_key": settings.TURNSTILE_SITE_KEY if turnstile_enabled() else "",
    }
