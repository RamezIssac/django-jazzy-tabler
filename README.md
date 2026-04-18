# django-jazzy-tabler

A drop-in Django admin theme built on [Tabler.io](https://tabler.io) (Bootstrap 5).
Inspired by [django-jazzmin](https://github.com/farridav/django-jazzmin) — same configuration surface, different skin.

> **Status:** early alpha. API and templates may change.

## Install

```bash
pip install django-jazzy-tabler   # or: uv add django-jazzy-tabler
```

Add to `INSTALLED_APPS` **before** `django.contrib.admin`:

```python
INSTALLED_APPS = [
    "jazzy_tabler",
    "django.contrib.admin",
    # ...
]
```

That's it. Templates resolve ahead of the stock admin automatically.

## Configure

All options are optional. Drop a `JAZZY_SETTINGS` (and/or `JAZZY_UI_TWEAKS`) dict in `settings.py`:

```python
JAZZY_SETTINGS = {
    "site_title": "My Admin",
    "site_header": "Acme",
    "site_brand": "Acme",
    "welcome_sign": "Welcome back",
    "search_model": "auth.User",
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "blog.post": "fas fa-newspaper",
    },
    "changeform_format": "horizontal_tabs",   # single | horizontal_tabs | vertical_tabs | carousel | collapsible
    "changeform_show_buttons_below": False,   # True = submit row in-card at the bottom; False = sidebar
}

JAZZY_UI_TWEAKS = {
    "navbar": "light",          # or "dark"
    "sidebar": "dark",
    "default_theme_mode": "light",  # light | dark | auto
    "accent_color": "primary",
}
```

If you're migrating from jazzmin, `JAZZMIN_SETTINGS` is also read as a fallback — you can switch themes by toggling `INSTALLED_APPS`.

## Develop

The repo ships a `demo/` Django project and a test suite.

```bash
uv sync
uv run pytest                                    # run tests
uv run python manage.py migrate --run-syncdb
uv run python manage.py createsuperuser
uv run python manage.py runserver                # browse /admin/
```

## Credits

This theme is only possible because of [**Tabler**](https://tabler.io) — a beautiful, open-source dashboard UI kit. If you use and enjoy `django-jazzy-tabler`, please:

- ⭐ Star this repo if it saved you time — it helps others find the theme
- ⭐ Star the [Tabler repo](https://github.com/tabler/tabler)
- 💛 [Sponsor Tabler](https://github.com/sponsors/codecalm) to keep the upstream UI kit alive


## License

MIT
