"""Coverage matrix, layer 2: screenshots of the admin pages the theme renders.

Opt-in browser pass (Playwright/Chromium). Run it with:

    uv sync --group screenshots
    uv run playwright install chromium   # once
    JAZZY_SCREENSHOTS=1 uv run pytest tests/test_screenshots.py

Output lands in ``proofs/<run>/`` (run name via ``JAZZY_PROOFS_RUN``, default
``latest``): ``light/`` + ``dark/`` PNGs, a machine-readable ``manifest.json``,
and an ``index.html`` review site (4-column inline grid, titles = page slugs).

Matrix shape (per captain's review):
- light: the full inventory, minus noisy filter variants (those stay covered
  by the always-on URL suite), plus interaction shots and the stacked
  (changeform_format=single) change-form variant
- dark: the main pages only — index, changelist, change form
- the 404/500 previews stay in the matrix so their templates are reviewable

HARD RULE for agents: screenshots are handled by filesystem path only. Never
open/read the PNG files themselves; verify captures via file existence/size
and DOM/computed-style assertions (see tests/test_widget_layout.py).
"""

import json
import os
import re
from pathlib import Path

import pytest

from .conftest import (
    fresh_context,
    login,
    requires_screenshots,
)

pytestmark = [pytest.mark.screenshots, requires_screenshots]

PROOFS_ROOT = Path("proofs")
RUN = os.environ.get("JAZZY_PROOFS_RUN", "latest")

# Dark mode: main pages only.
DARK_SLUGS = {"index", "blog-post-changelist", "blog-post-change"}

# Stacked (changeform_format=single) variants captured against stacked_server.
STACKED_PAGES = [
    ("/admin/blog/post/add/", "blog-post-add-stacked", "Post add — stacked layout"),
    (None, "blog-post-change-stacked", "Post change — stacked layout"),  # url from inventory
]

# Interactive states worth capturing on top of the plain URL inventory (light).
INTERACTION_SHOTS = [
    {
        "slug": "blog-post-add-select2-category-open",
        "url": "/admin/blog/post/add/",
        "name": "Post add — autocomplete select2 dropdown open",
        "action": "open-select2-category",
    },
    {
        "slug": "blog-post-add-select2-author-open",
        "url": "/admin/blog/post/add/",
        "name": "Post add — plain select2 dropdown open",
        "action": "open-select2-author",
    },
]


class ConsoleTap:
    """Routes browser console errors into whichever manifest record is active."""

    def __init__(self):
        self.record = None

    def attach(self, page):
        page.on("console", self._on_console)
        page.on("pageerror", self._on_pageerror)

    def _on_console(self, msg):
        # favicon 404s on the dev server are noise, not regressions
        if self.record is not None and msg.type == "error" and "favicon" not in msg.text:
            self.record["console_errors"].append(msg.text)

    def _on_pageerror(self, exc):
        if self.record is not None:
            self.record["console_errors"].append(f"pageerror: {exc}")


def _shot(page, out_dir: Path, slug: str) -> dict:
    path = out_dir / f"{slug}.png"
    page.screenshot(path=str(path))
    return {"file": str(path), "bytes": path.stat().st_size}


def _run_action(page, action: str):
    if action == "open-select2-category":
        page.click("#id_category + .select2-container, .field-category .select2-container")
        page.wait_for_selector(".select2-container--open")
    elif action == "open-select2-author":
        page.click(".field-author .select2-container")
        page.wait_for_selector(".select2-container--open")
    else:  # pragma: no cover - configuration error
        raise ValueError(f"unknown action {action}")


def _capture(page, tap, base_url, slug, url, name, expected_status, out_dir, manifest, mode):
    record = {"mode": mode, "slug": slug, "url": url, "name": name, "console_errors": []}
    tap.record = record
    response = page.goto(f"{base_url}{url}", wait_until="networkidle")
    status = response.status if response is not None else 0
    record["status"] = status
    assert status == expected_status, f"[{mode}] {slug}: {url} -> {status} (expected {expected_status})"
    assert page.evaluate("document.documentElement.getAttribute('data-bs-theme')") == mode
    record.update(_shot(page, out_dir, slug))
    assert record["bytes"] > 10_000, f"[{mode}] {slug}: suspiciously small screenshot"
    manifest.append(record)
    tap.record = None
    return record


def _capture_inventory(page, tap, base_url, inventory, out_dir, manifest, mode):
    for entry in inventory:
        _capture(
            page, tap, base_url,
            entry["slug"], entry["url"], entry["name"], entry["expected_status"],
            out_dir, manifest, mode,
        )


def _capture_logout(page, base_url, out_dir, manifest, mode):
    page.goto(f"{base_url}/admin/", wait_until="networkidle")
    page.click("header a[aria-label='Account']")
    with page.expect_navigation():
        page.click("#logout-form button[type=submit]")
    record = {"mode": mode, "slug": "logout", "url": "/admin/logout/", "name": "Logged out",
              "status": 200, "console_errors": []}
    record.update(_shot(page, out_dir, "logout"))
    manifest.append(record)


def _write_review_index(run_dir: Path, manifest: list[dict], run: str):
    import html
    from collections import OrderedDict

    def grid(entries):
        figures = []
        for entry in entries:
            rel = Path(entry["file"]).relative_to(run_dir)
            warn = f" <span class='warn'>⚠ console: {html.escape('; '.join(entry['console_errors']))}</span>" if entry["console_errors"] else ""
            figures.append(
                "<figure>"
                f"<figcaption><code>{html.escape(entry['slug'])}</code>"
                f"<span class='meta'>{entry.get('status', '')} · {entry['bytes']:,} B</span>{warn}</figcaption>"
                f"<a href=\"{rel}\"><img loading=\"lazy\" src=\"{rel}\" alt=\"{html.escape(entry['name'])}\"></a>"
                "</figure>"
            )
        return f"<div class='grid'>{''.join(figures)}</div>"

    by_mode: dict[str, list] = OrderedDict((mode, []) for mode in ("light", "dark"))
    for entry in manifest:
        by_mode.setdefault(entry["mode"], []).append(entry)

    sections = []
    titles = {"light": "Light — full matrix", "dark": "Dark — main pages"}
    for mode, entries in by_mode.items():
        sections.append(f"<h2>{titles.get(mode, mode)} <span class='meta'>({len(entries)} pages)</span></h2>{grid(entries)}")

    page = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>jazzy-tabler matrix — {html.escape(run)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 1.5rem; color: #1f2937; background: #f9fafb; }}
h1 {{ font-size: 1.4rem; }} h2 {{ font-size: 1.1rem; margin-top: 2rem; }}
.meta {{ color: #6b7280; font-weight: 400; font-size: 0.75rem; margin-left: .5rem; }}
.warn {{ color: #b45309; font-size: 0.75rem; display: block; }}
.grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }}
figure {{ margin: 0; }}
figcaption {{ font-size: 0.78rem; margin-bottom: 0.3rem; }}
figure img {{ width: 100%; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; }}
code {{ background: #eef2f7; padding: 0.05rem 0.3rem; border-radius: 4px; }}
</style></head><body>
<h1>django-jazzy-tabler — admin screenshot matrix</h1>
<p class="meta">Run: <strong>{html.escape(run)}</strong> · {len(manifest)} captures ·
desktop 1440×900 · generated by <code>tests/test_screenshots.py</code>
(<code>JAZZY_SCREENSHOTS=1 uv run pytest tests/test_screenshots.py</code>)</p>
{''.join(sections)}
</body></html>"""
    (run_dir / "index.html").write_text(page)


def test_screenshot_matrix(demo_server, stacked_server, browser):
    run_dir = PROOFS_ROOT / RUN
    manifest: list[dict] = []
    inventory = [p for p in demo_server.inventory if p.get("screenshot", True)]

    # ---- light: full matrix -------------------------------------------------
    out_dir = run_dir / "light"
    out_dir.mkdir(parents=True, exist_ok=True)
    context = fresh_context(browser, demo_server.base_url, "light")
    page = context.new_page()
    tap = ConsoleTap()
    tap.attach(page)

    anon = [p for p in inventory if p["anonymous"]]
    auth = [p for p in inventory if not p["anonymous"]]
    _capture_inventory(page, tap, demo_server.base_url, anon, out_dir, manifest, "light")

    login(page, demo_server.base_url)
    _capture_inventory(page, tap, demo_server.base_url, auth, out_dir, manifest, "light")

    for shot in INTERACTION_SHOTS:
        page.goto(f"{demo_server.base_url}{shot['url']}", wait_until="networkidle")
        _run_action(page, shot["action"])
        record = {"mode": "light", "slug": shot["slug"], "url": shot["url"], "name": shot["name"],
                  "status": 200, "console_errors": []}
        record.update(_shot(page, out_dir, shot["slug"]))
        manifest.append(record)

    _capture_logout(page, demo_server.base_url, out_dir, manifest, "light")
    context.close()

    # ---- light: stacked changeform variant ----------------------------------
    context = fresh_context(browser, stacked_server.base_url, "light")
    page = context.new_page()
    tap = ConsoleTap()
    tap.attach(page)
    login(page, stacked_server.base_url)
    change_url = next(p["url"] for p in stacked_server.inventory if p["slug"] == "blog-post-change")
    for url, slug, name in STACKED_PAGES:
        url = url or change_url
        _capture(page, tap, stacked_server.base_url, slug, url, name, 200, out_dir, manifest, "light")
    context.close()

    # ---- dark: main pages only ----------------------------------------------
    out_dir = run_dir / "dark"
    out_dir.mkdir(parents=True, exist_ok=True)
    context = fresh_context(browser, demo_server.base_url, "dark")
    page = context.new_page()
    tap = ConsoleTap()
    tap.attach(page)
    login(page, demo_server.base_url)
    dark_pages = [p for p in inventory if p["slug"] in DARK_SLUGS]
    assert len(dark_pages) == len(DARK_SLUGS), f"missing dark pages: {DARK_SLUGS - {p['slug'] for p in dark_pages}}"
    _capture_inventory(page, tap, demo_server.base_url, dark_pages, out_dir, manifest, "dark")
    context.close()

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    _write_review_index(run_dir, manifest, RUN)

    # fail loudly on JS errors — this is how Tabler-upgrade regressions surface
    def expected_document_error(m, msg):
        # pages with a non-200 expected status (404/500 previews) log the
        # document load as a console resource error — that's the point of them
        return m.get("status") != 200 and "Failed to load resource" in msg and f"status of {m.get('status')}" in msg

    js_errors = [
        f"[{m['mode']}] {m['slug']}: {e}"
        for m in manifest
        for e in m["console_errors"]
        if not expected_document_error(m, e)
    ]
    js_errors = [e for e in js_errors if not re.search(r"favicon|net::ERR", e)]
    assert not js_errors, "Browser console errors during screenshot matrix:\n" + "\n".join(js_errors)
