import pytest
from django.test import override_settings


@pytest.mark.django_db
def test_sidebar_lists_default_auth_app_and_models(admin_client):
    response = admin_client.get("/admin/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Authentication and Authorization" in content
    assert "Users" in content
    assert "Groups" in content


@pytest.mark.django_db
def test_sidebar_lists_demo_blog_app_and_models(admin_client):
    response = admin_client.get("/admin/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Blog" in content
    assert "Posts" in content
    assert "Categories" in content


@pytest.mark.django_db
def test_sidebar_uses_tabler_dropdown_markup(admin_client):
    response = admin_client.get("/admin/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'class="nav-item dropdown"' in content
    assert 'class="nav-link dropdown-toggle"' in content
    assert 'data-bs-toggle="dropdown"' in content
    assert 'class="dropdown-menu"' in content
    assert 'class="dropdown-item"' in content
    assert 'text-uppercase text-muted fw-bold' not in content


@pytest.mark.django_db
@override_settings(JAZZY_UI_TWEAKS={"accent_color": "azure"})
def test_accent_color_tweak_recolors_sidebar_active_item(admin_client):
    response = admin_client.get("/admin/")
    assert response.status_code == 200
    assert "--tblr-azure" in response.content.decode()


@pytest.mark.django_db
def test_accent_color_defaults_to_primary_without_override(admin_client):
    response = admin_client.get("/admin/")
    assert response.status_code == 200
    assert "#jazzy-sidebar .nav-link.active" not in response.content.decode()
