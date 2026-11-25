"""Cloudflare Turnstile on the admin login, verified server-side; off when the keys are unset."""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django import forms
from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm

from demo.live.client_ip import client_ip

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
log = logging.getLogger(__name__)


def turnstile_enabled() -> bool:
    return bool(settings.TURNSTILE_SITE_KEY and settings.TURNSTILE_SECRET_KEY)


def verify_token(token: str, remote_ip: str) -> bool:
    payload = urllib.parse.urlencode(
        {"secret": settings.TURNSTILE_SECRET_KEY, "response": token, "remoteip": remote_ip}
    ).encode()
    try:
        with urllib.request.urlopen(SITEVERIFY_URL, data=payload, timeout=10) as response:
            return bool(json.load(response).get("success"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        log.exception("Turnstile verification could not reach Cloudflare")
        return False


class TurnstileAuthenticationForm(AdminAuthenticationForm):
    """Admin login form that checks the Turnstile token before the credentials are tried."""

    def clean(self):
        if turnstile_enabled():
            token = self.data.get("cf-turnstile-response", "")
            if not token or not verify_token(token, client_ip(self.request)):
                raise forms.ValidationError("Captcha check failed. Reload the page and try again.", code="captcha")
        return super().clean()
