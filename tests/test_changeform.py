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
def test_changeform_submit_buttons_default_to_sidebar(admin_client):
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
