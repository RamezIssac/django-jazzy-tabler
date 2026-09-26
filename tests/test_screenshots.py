"""Coverage matrix, layer 2: screenshots of every inventoried admin URL.

Opt-in browser pass (Playwright/Chromium). Run it with:

    uv sync --group screenshots
    uv run playwright install chromium   # once
    JAZZY_SCREENSHOTS=1 uv run pytest tests/test_screenshots.py

Output lands in ``proofs/<run>/`` (run name via ``JAZZY_PROOFS_RUN``, default
``latest``): ``light/`` and ``dark/`` PNGs plus ``manifest.json`` and an
``index.html`` review page.

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

THEME_MODES = ("light", "dark")

PROOFS_ROOT = Path("proofs")
RUN = os.environ.get("JAZZY_PROOFS_RUN", "latest")

# Interactive states worth capturing on top of the plain URL inventory.
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


def _capture_inventory(page, tap, base_url, inventory, out_dir, manifest, mode):
    for entry in inventory:
        record = {"mode": mode, **{k: entry[k] for k in ("slug", "url", "name")}, "console_errors": []}
        tap.record = record

        response = page.goto(f"{base_url}{entry['url']}", wait_until="networkidle")
        status = response.status if response is not None else 0
        record["status"] = status
        assert status == entry["expected_status"], (
            f"[{mode}] {entry['slug']}: {entry['url']} -> {status} (expected {entry['expected_status']})"
        )
        assert page.evaluate("document.documentElement.getAttribute('data-bs-theme')") == mode

        record.update(_shot(page, out_dir, entry["slug"]))
        assert record["bytes"] > 10_000, f"[{mode}] {entry['slug']}: suspiciously small screenshot"
        manifest.append(record)
        tap.record = None


def _capture_logout(page, base_url, out_dir, manifest, mode):
    record = {"mode": mode, "slug": "logout", "url": "/admin/logout/", "name": "Logged out", "console_errors": []}
    page.goto(f"{base_url}/admin/", wait_until="networkidle")
    page.click("header a[aria-label='Account']")
    with page.expect_navigation():
        page.click("#logout-form button[type=submit]")
    record["status"] = 200
    record.update(_shot(page, out_dir, "logout"))
    manifest.append(record)


def _write_review_index(run_dir: Path, manifest: list[dict], run: str):
    import html

    rows = []
    for entry in manifest:
        rel = Path(entry["file"]).relative_to(run_dir)
        errors = "; ".join(entry["console_errors"])
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(entry['slug'])}</code></td>"
            f"<td>{html.escape(entry['name'])}</td>"
            f"<td><a href=\"{html.escape(entry['url'])}\">{html.escape(entry['url'])}</a></td>"
            f"<td>{entry['mode']}</td>"
            f"<td>{entry.get('status', '')}</td>"
            f"<td>{entry['bytes']:,}</td>"
            f"<td><a href=\"{rel}\">png</a></td>"
            f"<td>{'⚠️ ' + html.escape(errors) if errors else ''}</td>"
            "</tr>"
        )
    modes = ", ".join(THEME_MODES)
    page = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>jazzy-tabler proofs — {html.escape(run)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
th, td {{ border: 1px solid #d1d5db; padding: 0.35rem 0.6rem; text-align: left; }}
th {{ background: #f3f4f6; }}
</style></head><body>
<h1>django-jazzy-tabler — screenshot matrix</h1>
<p>Run: <strong>{html.escape(run)}</strong> · modes: {modes} · {len(manifest)} captures.
Open the <code>png</code> links relative to this file.</p>
<table>
<tr><th>slug</th><th>page</th><th>url</th><th>mode</th><th>status</th><th>bytes</th><th>shot</th><th>console</th></tr>
{''.join(rows)}
</table>
</body></html>"""
    (run_dir / "index.html").write_text(page)


def test_screenshot_matrix(demo_server, browser):
    run_dir = PROOFS_ROOT / RUN
    manifest: list[dict] = []
    inventory = demo_server.inventory

    for mode in THEME_MODES:
        out_dir = run_dir / mode
        out_dir.mkdir(parents=True, exist_ok=True)

        context = fresh_context(browser, demo_server.base_url, mode)
        page = context.new_page()
        tap = ConsoleTap()
        tap.attach(page)

        # anonymous pages first (a logged-in session redirects away from login)
        anon = [p for p in inventory if p["anonymous"]]
        auth = [p for p in inventory if not p["anonymous"]]
        _capture_inventory(page, tap, demo_server.base_url, anon, out_dir, manifest, mode)

        login(page, demo_server.base_url)
        _capture_inventory(page, tap, demo_server.base_url, auth, out_dir, manifest, mode)

        for shot in INTERACTION_SHOTS:
            record = {"mode": mode, **{k: shot[k] for k in ("slug", "url", "name")}, "console_errors": []}
            page.goto(f"{demo_server.base_url}{shot['url']}", wait_until="networkidle")
            _run_action(page, shot["action"])
            record["status"] = 200
            record.update(_shot(page, out_dir, shot["slug"]))
            manifest.append(record)

        _capture_logout(page, demo_server.base_url, out_dir, manifest, mode)
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
