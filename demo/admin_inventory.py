"""Admin URL inventory — the single source of truth for the coverage matrix.

Everything is derived from the registered admin site plus the seeded demo data,
so the inventory grows automatically as models/admins are added.

Consumed by:
- ``tests/test_admin_urls.py`` — fast Django test-client suite (every URL renders)
- ``manage.py dump_admin_inventory`` — JSON export used by the Playwright
  screenshot matrix in ``tests/test_screenshots.py``
"""

from dataclasses import asdict, dataclass

from django.contrib import admin
from django.db import models
from django.urls import reverse


@dataclass
class Page:
    slug: str  # unique, file-safe identifier (used for screenshot filenames)
    url: str
    name: str  # human-readable label
    expected_status: int = 200
    anonymous: bool = False  # fetch without an authenticated session
    screenshot: bool = True  # include in the screenshot matrix (URL suite always covers all)


def _changelist_extras(model, model_admin, prefix: str, changelist_url: str) -> list[Page]:
    """Filtered / searched / paginated changelist states, derived from the admin config."""
    extras: list[Page] = []

    if model_admin.search_fields:
        extras.append(
            Page(f"{prefix}-changelist-search", f"{changelist_url}?q=seed", f"{prefix} changelist (search)")
        )

    if model._default_manager.count() > model_admin.list_per_page:
        extras.append(
            Page(f"{prefix}-changelist-page2", f"{changelist_url}?p=2", f"{prefix} changelist (page 2)")
        )

    if model_admin.date_hierarchy:
        field_name = model_admin.date_hierarchy
        dt = (
            model._default_manager.exclude(**{f"{field_name}__isnull": True})
            .order_by(field_name)
            .values_list(field_name, flat=True)
            .first()
        )
        if dt is not None:
            extras.append(
                Page(
                    f"{prefix}-changelist-date-hierarchy",
                    f"{changelist_url}?{field_name}__year={dt.year}",
                    f"{prefix} changelist (date hierarchy {dt.year})",
                )
            )

    for entry in model_admin.list_filter:
        if not isinstance(entry, str):
            continue  # custom ListFilter classes can't be derived generically
        field = model._meta.get_field(entry)
        if field.choices:
            url = f"{changelist_url}?{entry}__exact={field.choices[0][0]}"
        elif isinstance(field, models.BooleanField):
            url = f"{changelist_url}?{entry}__exact=1"
        elif isinstance(field, (models.ForeignKey, models.ManyToManyField)):
            related = field.related_model._default_manager.order_by("pk").first()
            if related is None:
                continue
            url = f"{changelist_url}?{entry}__id__exact={related.pk}"
        elif isinstance(field, models.DateField):  # covers DateTimeField too
            dt = (
                model._default_manager.exclude(**{f"{entry}__isnull": True})
                .order_by(entry)
                .values_list(entry, flat=True)
                .first()
            )
            if dt is None:
                continue
            url = f"{changelist_url}?{entry}__year={dt.year}"
        else:
            continue
        extras.append(Page(f"{prefix}-changelist-filter-{entry}", url, f"{prefix} changelist (filter: {entry})", screenshot=False))

    return extras


def build_inventory() -> list[Page]:
    site = admin.site
    pages = [
        Page("login", reverse("admin:login"), "Login", anonymous=True),
        Page("index", reverse("admin:index"), "Dashboard"),
        Page("password-change", reverse("admin:password_change"), "Password change"),
        Page("password-change-done", reverse("admin:password_change_done"), "Password change done"),
        Page("preview-404", "/preview/404/", "404 template", expected_status=404),
        Page("preview-500", "/preview/500/", "500 template", expected_status=500),
    ]

    apps: dict[str, list] = {}
    for model, model_admin in site._registry.items():
        apps.setdefault(model._meta.app_label, []).append((model, model_admin))

    for app_label in sorted(apps):
        pages.append(Page(f"app-{app_label}", f"/admin/{app_label}/", f"App index: {app_label}"))
        for model, model_admin in sorted(apps[app_label], key=lambda pair: pair[0]._meta.model_name):
            opts = model._meta
            url_prefix = f"admin:{opts.app_label}_{opts.model_name}"
            prefix = f"{opts.app_label}-{opts.model_name}"
            label = f"{opts.app_label}.{opts.model_name}"

            changelist_url = reverse(f"{url_prefix}_changelist")
            pages.append(Page(f"{prefix}-changelist", changelist_url, f"{label} changelist"))
            pages.extend(_changelist_extras(model, model_admin, prefix, changelist_url))
            pages.append(Page(f"{prefix}-add", reverse(f"{url_prefix}_add"), f"{label} add"))

            obj = model._default_manager.order_by("pk").first()
            if obj is None:
                continue
            args = [obj.pk]
            pages.append(Page(f"{prefix}-change", reverse(f"{url_prefix}_change", args=args), f"{label} change"))
            pages.append(Page(f"{prefix}-delete", reverse(f"{url_prefix}_delete", args=args), f"{label} delete"))
            pages.append(Page(f"{prefix}-history", reverse(f"{url_prefix}_history", args=args), f"{label} history"))

    return pages


def inventory_as_json() -> str:
    import json

    return json.dumps([asdict(page) for page in build_inventory()], indent=2)
