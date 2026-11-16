import copy

import pytest


@pytest.mark.django_db
def test_navbar_extra_hook_renders_empty_by_default(admin_client):
    """The default include ships empty: hook renders nothing, page still renders."""
    response = admin_client.get("/admin/")

    assert response.status_code == 200
    content = response.content.decode()
    assert '<header class="navbar navbar-expand-md' in content
    assert "jazzy-navbar-extra-sample" not in content


@pytest.mark.django_db
def test_navbar_extra_override_content_appears_in_navbar(admin_client, tmp_path, settings):
    """An app overriding jazzy_tabler/includes/navbar_extra.html gets its content
    rendered in the top navbar — desktop header and the mobile d-lg-none nav."""
    include_dir = tmp_path / "templates" / "jazzy_tabler" / "includes"
    include_dir.mkdir(parents=True)
    (include_dir / "navbar_extra.html").write_text(
        '<div class="nav-item d-none d-md-flex me-3">'
        '<a class="btn btn-ghost-secondary" href="/guide/" '
        'id="jazzy-navbar-extra-sample">Guide</a>'
        "</div>"
    )
    templates = copy.deepcopy(settings.TEMPLATES)
    templates[0]["DIRS"] = [str(tmp_path / "templates")]
    settings.TEMPLATES = templates

    response = admin_client.get("/admin/")

    assert response.status_code == 200
    content = response.content.decode()
    # Desktop top navbar and the mobile (d-lg-none) navbar both render the include.
    assert content.count('id="jazzy-navbar-extra-sample"') == 2
    assert content.index('id="jazzy-navbar-extra-sample"') < content.index("jazzy-mode-toggle")
