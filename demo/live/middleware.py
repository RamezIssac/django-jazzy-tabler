import logging
import time
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone

from demo.seed import ensure_viewer, reset

log = logging.getLogger(__name__)
SAFE_METHODS = ("GET", "HEAD", "OPTIONS")
RESET_CHECK_SECONDS = 60


def read_only_demo(get_response):
    """The shared demo account may browse and log out; every other write and the password change are refused."""

    def middleware(request):
        if request.user.is_authenticated and request.user.get_username() == settings.DEMO_USERNAME:
            is_write = request.method not in SAFE_METHODS and request.path != reverse("admin:logout")
            if is_write or request.path == reverse("admin:password_change"):
                return HttpResponseForbidden("The demo account is read-only.")
        return get_response(request)

    return middleware


def reset_if_due():
    from demo.live.models import DemoReset

    def is_due(reset_at):
        return reset_at is None or timezone.now() - reset_at >= timedelta(hours=settings.DEMO_RESET_HOURS)

    if not is_due(DemoReset.objects.values_list("reset_at", flat=True).get(pk=1)):
        return
    with transaction.atomic():
        marker = DemoReset.objects.select_for_update().get(pk=1)
        if not is_due(marker.reset_at):  # another worker reset while this one waited for the lock
            return
        summary = reset()
        ensure_viewer(settings.DEMO_USERNAME, settings.DEMO_PASSWORD)
        marker.reset_at = timezone.now()
        marker.save(update_fields=["reset_at"])
    log.info("Demo data reset: %s", summary)
    if settings.SENTRY_DSN:
        import sentry_sdk

        sentry_sdk.capture_message("Demo data reset", level="info")


def demo_reset(get_response):
    """Reseed the demo and restore the demo account once DEMO_RESET_HOURS have passed; each worker checks once a minute."""
    next_check = 0.0

    def middleware(request):
        nonlocal next_check
        if time.monotonic() >= next_check:
            next_check = time.monotonic() + RESET_CHECK_SECONDS
            reset_if_due()
        return get_response(request)

    return middleware
