import pytest
from django.test import override_settings

from demo.blog.models import Category, Post


@pytest.mark.django_db
def test_changeform_renders_for_add(admin_client):
    response = admin_client.get("/admin/blog/post/add/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="post_form"' in content
    assert "csrfmiddlewaretoken" in content
    assert 'name="_save"' in content
    assert "Add post" in content
    assert 'name="title"' in content
    assert 'name="body"' in content
    assert 'name="category"' in content


@pytest.mark.django_db
def test_changeform_renders_for_edit(admin_client):
    category = Category.objects.create(name="News")
    post = Post.objects.create(title="Hello world", body="Body text", category=category)

    response = admin_client.get(f"/admin/blog/post/{post.pk}/change/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="post_form"' in content
    assert 'name="_save"' in content
    assert 'name="title"' in content
    assert 'value="Hello world"' in content
    assert "Body text" in content


@pytest.mark.django_db
@override_settings(JAZZY_SETTINGS={})
def test_changeform_submit_buttons_below_by_default(admin_client):
    """The shipped default renders the submit row below the form (card footer)."""
    response = admin_client.get("/admin/blog/post/add/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "jazzy-actions-bottom" in content
    assert 'id="jazzy-actions"' not in content


@pytest.mark.django_db
@override_settings(JAZZY_SETTINGS={"changeform_show_buttons_below": False})
def test_changeform_submit_buttons_in_sidebar_when_disabled(admin_client):
    response = admin_client.get("/admin/blog/post/add/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="jazzy-actions"' in content
    assert "jazzy-actions-bottom" not in content


@pytest.mark.django_db
@override_settings(JAZZY_SETTINGS={"changeform_show_buttons_below": True})
def test_changeform_submit_buttons_below_when_enabled(admin_client):
    response = admin_client.get("/admin/blog/post/add/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "jazzy-actions-bottom" in content
    assert 'id="jazzy-actions"' not in content
    assert content.index('name="_save"') > content.index('name="title"')


@pytest.mark.django_db
def test_related_widget_icons_are_theme_font_glyphs(admin_client):
    """FK related-object links are inline FontAwesome glyphs (currentColor),
    not <img> SVGs with hardcoded colors that ignore the theme."""
    import re

    response = admin_client.get("/admin/blog/post/add/")

    assert response.status_code == 200
    content = response.content.decode()
    wrappers = re.findall(r'<div class="related-widget-wrapper".*?</div>', content, re.S)
    assert wrappers, "expected related-widget-wrapper markup on the post form"
    for wrapper in wrappers:
        assert "<img" not in wrapper, "related links must not use <img> icons"
    for css_class in ("fa-plus", "fa-pen", "fa-xmark", "fa-eye"):
        assert f'"fas {css_class}"' in content


@pytest.mark.django_db
def test_inline_management_form_rendered_exactly_once(admin_client):
    """Regression: the changeform layout includes used to render
    formset.management_form AND include the inline template (which renders it
    again), producing duplicate #id_*-TOTAL_FORMS elements."""
    category = Category.objects.create(name="News")
    Post.objects.create(title="Hello world", body="Body text", category=category)

    response = admin_client.get(f"/admin/blog/category/{category.pk}/change/")

    assert response.status_code == 200
    content = response.content.decode()
    assert content.count('name="posts-TOTAL_FORMS"') == 1
    assert content.count('id="id_posts-TOTAL_FORMS"') == 1


@pytest.mark.django_db
def test_changeform_renders_tabular_inline_formset(admin_client):
    category = Category.objects.create(name="News")
    Post.objects.create(title="Hello world", body="Body text", category=category)

    response = admin_client.get(f"/admin/blog/category/{category.pk}/change/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="posts-group"' in content
    assert 'data-inline-type="tabular"' in content
    assert 'name="posts-TOTAL_FORMS"' in content
    assert 'name="posts-0-title"' in content
    assert 'value="Hello world"' in content
