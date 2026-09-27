"""Deterministic demo data.

Used by the ``seed_demo`` management command (demo server, screenshot matrix)
and by the test suites, so every admin view always renders meaningfully.
"""

import random
from datetime import datetime, timedelta, timezone

CATEGORIES = ["News", "Tutorials", "Releases", "Opinions", "Events"]
TAGS = ["python", "django", "tabler", "css", "release", "tutorial", "community", "howto"]
AUTHORS = [
    ("Ada Lovelace", "ada@example.com"),
    ("Grace Hopper", "grace@example.com"),
    ("Alan Turing", "alan@example.com"),
    ("Edsger Dijkstra", "edsger@example.com"),
    ("Barbara Liskov", "barbara@example.com"),
    ("Donald Knuth", "donald@example.com"),
]
POST_COUNT = 26  # > PostAdmin.list_per_page, so the changelist paginates
STATUSES = ["published", "draft", "published", "archived", "published"]


def seed(create_superuser: bool = False, verbosity: int = 1) -> dict:
    """Create the demo dataset. Idempotent: does nothing when posts already exist."""
    from django.contrib.admin.models import CHANGE, LogEntry
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from demo.blog.models import Author, Category, Comment, Post, Tag

    summary = {"created": False}
    if Post.objects.exists():
        return summary

    rng = random.Random(42)
    base = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)

    categories = [Category.objects.create(name=n, slug=n.lower()) for n in CATEGORIES]
    tags = [Tag.objects.create(name=n) for n in TAGS]
    authors = [
        Author.objects.create(
            name=name,
            email=email,
            bio=f"{name} writes about software, design and open source.",
        )
        for name, email in AUTHORS
    ]

    posts = []
    for i in range(POST_COUNT):
        status = STATUSES[i % len(STATUSES)]
        post = Post.objects.create(
            title=f"Seed post {i + 1:02d}: {CATEGORIES[i % len(CATEGORIES)]} digest",
            body=(
                f"This is the seeded body of post {i + 1}.\n\n"
                "It exists so every admin view — changelist, filters, search, "
                "history, inlines — has something meaningful to render."
            ),
            category=categories[i % len(categories)],
            author=authors[i % len(authors)],
            status=status,
            is_featured=(i % 5 == 0),
            views=rng.randint(0, 9000),
            published_at=base + timedelta(days=23 * i) if status != "draft" else None,
        )
        post.tags.set([tags[i % len(tags)], tags[(i + 3) % len(tags)]])
        posts.append(post)

    for post in posts[:12]:
        for j in range(rng.randint(1, 3)):
            Comment.objects.create(
                post=post,
                author_name=authors[(post.pk + j) % len(authors)].name,
                text=f"Seeded comment {j + 1} on “{post.title[:32]}…”.",
            )

    editors = Group.objects.create(name="Editors")
    viewers = Group.objects.create(name="Viewers")
    blog_permissions = Permission.objects.filter(content_type__app_label="blog")
    editors.permissions.set(blog_permissions)
    viewers.permissions.set(blog_permissions.filter(codename__startswith="view_"))

    User = get_user_model()
    editor = User.objects.create_user(
        username="editor", email="editor@example.com", password="unused", is_staff=True
    )
    editor.groups.add(editors)

    def log(obj, message, flag=CHANGE):
        LogEntry.objects.create(
            user_id=editor.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=str(obj.pk),
            object_repr=str(obj),
            action_flag=flag,
            change_message=message,
        )

    for post in posts[:10]:
        log(post, "Seeded change for the demo dashboard and history views.")
    # a couple of structured messages so the history view renders parsed entries too
    log(posts[0], '[{"changed": {"fields": ["title", "status"]}}]')
    log(posts[0], '[{"changed": {"fields": ["body"]}}]')
    # every inventoried history page (first object per model) gets an entry
    for obj in (categories[0], tags[0], authors[0], editors, editor):
        log(obj, "Seeded change so the history view has entries.")

    if create_superuser:
        import os

        password = os.environ.get("DEMO_ADMIN_PASSWORD", "admin")
        User.objects.create_superuser(
            username="admin", email="admin@example.com", password=password
        )
        summary["superuser"] = "admin"

    summary.update(
        {
            "created": True,
            "posts": Post.objects.count(),
            "categories": Category.objects.count(),
            "tags": Tag.objects.count(),
            "authors": Author.objects.count(),
            "comments": Comment.objects.count(),
        }
    )
    return summary
