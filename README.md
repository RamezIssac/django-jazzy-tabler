# django-jazzy-tabler

**A drop-in Django admin theme built on [Tabler](https://tabler.io) (Bootstrap 5) — with the settings you already know from [django-jazzmin](https://github.com/farridav/django-jazzmin).**

No build step, no Node, no npm. One `pip install`, two lines in `settings.py`, and your admin gets a clean, modern skin with first-class **light and dark mode**.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/RamezIssac/django-jazzy-tabler/main/docs/screenshots/dashboard-dark.png">
  <img alt="django-jazzy-tabler dashboard" src="https://raw.githubusercontent.com/RamezIssac/django-jazzy-tabler/main/docs/screenshots/dashboard-light.png">
</picture>

> **Status:** alpha. The configuration surface is stable enough to use; templates may still shift between minor versions.

## Why jazzy-tabler?

- **Drop-in.** Templates resolve ahead of `django.contrib.admin` — keep your `ModelAdmin`s exactly as they are.
- **Jazzmin-compatible settings.** A `JAZZY_SETTINGS` dict you may already have just works; `JAZZMIN_SETTINGS` is read as a fallback, so A/B testing the two themes is an `INSTALLED_APPS` toggle.
- **Light + dark, done properly.** Every screen is themed through Tabler CSS variables — including select2 dropdowns, autocomplete fields and the little FK add/change/view/delete icons.
- **Changeform layouts.** `single`, `horizontal_tabs`, `vertical_tabs`, `carousel`, `collapsible` — globally or per model.
- **Honest vendor stack.** Tabler 1.5.1 and FontAwesome 6 ship as static files inside the wheel. The admin works fully offline/air-gapped.
- **Tested against what you see.** The repo runs a URL-coverage suite (every admin page must render) plus an opt-in Playwright screenshot matrix over the whole admin, in both theme modes.

| Changelist | Change form |
|---|---|
| ![changelist, light](https://raw.githubusercontent.com/RamezIssac/django-jazzy-tabler/main/docs/screenshots/changelist-light.png) | ![change form, light](https://raw.githubusercontent.com/RamezIssac/django-jazzy-tabler/main/docs/screenshots/changeform-light.png) |
| ![changelist, dark](https://raw.githubusercontent.com/RamezIssac/django-jazzy-tabler/main/docs/screenshots/changelist-dark.png) | ![change form, dark](https://raw.githubusercontent.com/RamezIssac/django-jazzy-tabler/main/docs/screenshots/changeform-dark.png) |

## Quickstart

```bash
pip install django-jazzy-tabler   # or: uv add django-jazzy-tabler
```

Add `jazzy_tabler` to `INSTALLED_APPS` **before** `django.contrib.admin`:

```python
INSTALLED_APPS = [
    "jazzy_tabler",
    "django.contrib.admin",
    # ...
]
```

That's it — visit `/admin/`. Everything below is optional.

```python
# settings.py — all keys optional, all with sane defaults
JAZZY_SETTINGS = {
    "site_title": "Acme Admin",
    "site_header": "Acme",
    "site_brand": "Acme",
    "welcome_sign": "Welcome back",
    "search_model": "blog.Post",
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "blog.post": "fas fa-newspaper",
    },
    "changeform_format": "horizontal_tabs",
}

JAZZY_UI_TWEAKS = {
    "navbar": "light",
    "sidebar": "dark",
    "default_theme_mode": "light",   # light | dark | auto
    "accent_color": "primary",       # any Tabler color name
}
```

📖 **Full settings reference — every honored key, the jazzmin fallback rules, menu/icon structures, changeform formats, copy-pasteable examples:**
[docs/settings.md](https://github.com/RamezIssac/django-jazzy-tabler/blob/main/docs/settings.md)

## Compatibility

- Python 3.10+, Django 4.2+ (developed against the latest Django).
- Works with `autocomplete_fields`, `raw_id_fields`, `filter_horizontal`/`filter_vertical`, stacked + tabular inlines, and Django 4.1+ popup/related-object flows.

## Develop

The repo ships a `demo/` project and a two-layer test suite.

```bash
uv sync
uv run pytest                                        # fast suite: every admin URL must render

# demo server with seeded data
uv run python manage.py migrate --run-syncdb
uv run python manage.py seed_demo --with-superuser   # admin / admin (DEMO_ADMIN_PASSWORD to override)
uv run python manage.py runserver                    # browse http://127.0.0.1:8000/admin/

# opt-in browser pass: screenshot matrix over every admin page, light + dark
uv sync --group screenshots
uv run playwright install chromium                   # once
JAZZY_SCREENSHOTS=1 uv run pytest tests/test_screenshots.py
# -> proofs/latest/{light,dark}/*.png + manifest.json + index.html
```

## Credits

This theme is only possible because of [**Tabler**](https://tabler.io) — a beautiful, open-source dashboard UI kit. If you use and enjoy `django-jazzy-tabler`, please:

- ⭐ Star this repo if it saved you time — it helps others find the theme
- ⭐ Star the [Tabler repo](https://github.com/tabler/tabler)
- 💛 [Sponsor Tabler](https://github.com/sponsors/codecalm) to keep the upstream UI kit alive

## License

MIT
