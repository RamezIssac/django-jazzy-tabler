import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "demo-insecure-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "jazzy_tabler",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "demo.blog",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "demo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # DEMO_DATABASE lets the screenshot matrix run against a throwaway DB.
        "NAME": os.environ.get("DEMO_DATABASE", BASE_DIR / "demo.sqlite3"),
        "TEST": {"NAME": ":memory:"},
    }
}

MIGRATION_MODULES = {"blog": None}

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

JAZZY_SETTINGS = {
    "site_title": "Demo Admin",
    "site_header": "Jazzy Demo",
    "site_brand": "Jazzy Demo",
    "search_model": "blog.post",
    "changeform_show_buttons_below": True,
    "icons": {
        "blog": "fas fa-newspaper",
        "blog.post": "fas fa-file-alt",
        "blog.category": "fas fa-folder-open",
        "blog.tag": "fas fa-tags",
        "blog.author": "fas fa-user-edit",
        "blog.comment": "fas fa-comments",
    },
    "topmenu_links": [
        {"name": "404 Preview", "url": "preview_404", "icon": "fas fa-exclamation-triangle"},
        {"name": "500 Preview", "url": "preview_500", "icon": "fas fa-bug"},
    ],
}

# Screenshot matrix variant: DEMO_CHANGEFORM_FORMAT=single captures the stacked layout.
_changeform_format = os.environ.get("DEMO_CHANGEFORM_FORMAT")
if _changeform_format:
    JAZZY_SETTINGS["changeform_format"] = _changeform_format
