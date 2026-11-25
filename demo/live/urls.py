from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from demo.live.turnstile import TurnstileAuthenticationForm
from demo.urls import urlpatterns as demo_urlpatterns

admin.site.login_form = TurnstileAuthenticationForm
admin.site.login_template = "demo_live/login.html"

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    *demo_urlpatterns,
]
