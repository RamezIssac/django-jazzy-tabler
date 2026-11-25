"""The public live demo layer (demo/live): read-only account, data reset, Turnstile login form."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory

from demo.live.middleware import read_only_demo
from demo.live.turnstile import TurnstileAuthenticationForm
from demo.seed import ensure_viewer, reset


@pytest.fixture()
def guarded(settings):
    settings.DEMO_USERNAME = "demo"
    return read_only_demo(lambda request: HttpResponse("ok"))


def _request(method, path, user):
    request = getattr(RequestFactory(), method)(path)
    request.user = user
    return request


@pytest.mark.django_db
def test_demo_account_is_view_only_staff(seeded):
    user = ensure_viewer("demo", "pw")

    assert user.is_staff and not user.is_superuser
    assert user.get_all_permissions() == {f"blog.view_{m}" for m in ("post", "category", "tag", "author", "comment")}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("method", "path", "status"),
    [
        ("get", "/admin/blog/post/", 200),
        ("post", "/admin/blog/post/1/change/", 403),
        ("post", "/admin/blog/post/", 403),
        ("get", "/admin/password_change/", 403),
        ("post", "/admin/password_change/", 403),
        ("post", "/admin/logout/", 200),
    ],
)
def test_demo_account_can_only_browse_and_log_out(seeded, guarded, method, path, status):
    user = ensure_viewer("demo", "pw")

    assert guarded(_request(method, path, user)).status_code == status


@pytest.mark.django_db
def test_other_users_and_visitors_are_not_guarded(admin_user, guarded):
    assert guarded(_request("post", "/admin/blog/post/1/change/", admin_user)).status_code == 200
    assert guarded(_request("post", "/admin/login/", AnonymousUser())).status_code == 200


@pytest.mark.django_db
def test_reset_restores_the_seeded_data(seeded):
    from demo.blog.models import Post

    Post.objects.filter(pk__in=Post.objects.values("pk")[:5]).delete()
    Post.objects.update(title="defaced")

    summary = reset()

    assert summary["posts"] == 26
    assert not Post.objects.filter(title="defaced").exists()


@pytest.mark.django_db
def test_turnstile_refuses_a_login_without_a_token(settings, admin_user):
    settings.TURNSTILE_SITE_KEY, settings.TURNSTILE_SECRET_KEY = "site", "secret"
    request = RequestFactory().post("/admin/login/")
    form = TurnstileAuthenticationForm(request, data={"username": "admin", "password": "password"})

    assert not form.is_valid()
    assert "Captcha check failed" in str(form.errors)


@pytest.mark.django_db
def test_turnstile_is_off_without_keys(settings, admin_user):
    settings.TURNSTILE_SITE_KEY, settings.TURNSTILE_SECRET_KEY = "", ""
    request = RequestFactory().post("/admin/login/")
    form = TurnstileAuthenticationForm(request, data={"username": "admin", "password": "password"})

    assert form.is_valid()
