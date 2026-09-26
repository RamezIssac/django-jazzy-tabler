"""Coverage matrix, layer 1: every inventoried admin URL renders.

The inventory is derived from the registered admin site (see
``demo/admin_inventory.py``), so any admin page the theme can render is
asserted here. This is the durable "all admin URLs are covered" suite.
"""

import pytest
from django.test import Client

from demo.admin_inventory import build_inventory

MIN_INVENTORY_PAGES = 45  # sanity guard: the inventory must actually cover the site


@pytest.mark.django_db
def test_all_admin_urls_render(admin_client, seeded):
    anonymous_client = Client()
    pages = build_inventory()
    assert len(pages) >= MIN_INVENTORY_PAGES, f"inventory shrank unexpectedly: {len(pages)} pages"

    failures = []
    for page in pages:
        client = anonymous_client if page.anonymous else admin_client
        response = client.get(page.url)
        if response.status_code != page.expected_status:
            failures.append(
                f"{page.slug}: GET {page.url} -> {response.status_code} (expected {page.expected_status})"
            )
    assert not failures, "Broken admin pages:\n" + "\n".join(failures)


@pytest.mark.django_db
def test_admin_logout_via_post(admin_client, seeded):
    """Logout is POST-only in modern Django; the logged-out screen must render."""
    response = admin_client.post("/admin/logout/")
    assert response.status_code == 200
    assert "logged out" in response.content.decode().lower()


@pytest.mark.django_db
def test_admin_anonymous_redirects_to_login(client, seeded):
    response = client.get("/admin/")
    assert response.status_code == 302
    assert response["Location"].startswith("/admin/login/")


@pytest.mark.django_db
def test_login_redirects_to_admin_index(client, seeded, admin_user):
    """Regression: the login form must carry the hidden ``next`` field,
    otherwise Django falls back to LOGIN_REDIRECT_URL (/accounts/profile/ -> 404)."""
    response = client.post(
        "/admin/login/", {"username": admin_user.username, "password": "password", "next": "/admin/"}
    )
    assert response.status_code == 302
    assert response["Location"] == "/admin/"
