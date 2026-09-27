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

# Dedupe: near-identical pages add no new perspective (the always-on URL
# suite still covers them). blog-author/blog-tag duplicate blog-category's
# simple-model views; delete/history confirmations only differ per model for
# the rich demo model; the search state looks the same on every changelist.
DROPPED_SLUG_PREFIXES = ("blog-author-", "blog-tag-")
DROPPED_SLUGS = {
    "auth-user-delete",
    "auth-user-history",
    "auth-group-changelist",
    "auth-group-changelist-search",
    "auth-group-delete",
    "auth-group-history",
    "blog-category-delete",
    "blog-category-history",
}


def _notable(entry) -> bool:
    """Keep only pages that provide a new visual perspective."""
    slug = entry["slug"]
    if slug.startswith(DROPPED_SLUG_PREFIXES) or slug in DROPPED_SLUGS:
        return False
    if slug.endswith("-changelist-search") and slug != "blog-post-changelist-search":
        return False
    return True


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


def _shot(page, out_dir: Path, slug: str, full_page: bool = False) -> dict:
    path = out_dir / f"{slug}.png"
    page.screenshot(path=str(path), full_page=full_page)
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


def _capture(page, tap, base_url, slug, url, name, expected_status, out_dir, manifest, mode, full_page=False):
    record = {"mode": mode, "slug": slug, "url": url, "name": name, "console_errors": []}
    tap.record = record
    response = page.goto(f"{base_url}{url}", wait_until="networkidle")
    status = response.status if response is not None else 0
    record["status"] = status
    assert status == expected_status, f"[{mode}] {slug}: {url} -> {status} (expected {expected_status})"
    assert page.evaluate("document.documentElement.getAttribute('data-bs-theme')") == mode
    record.update(_shot(page, out_dir, slug, full_page=full_page))
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


def _group_of(entry) -> str:
    slug = entry["slug"]
    if entry["mode"] == "dark":
        return "dark"
    if slug.endswith("-stacked"):
        return "stacked"
    if "select2" in slug:
        return "interactions"
    if slug in ("login", "password-change", "password-change-done", "logout"):
        return "auth-pages"
    if slug == "index":
        return "dashboard"
    if slug.startswith("preview-"):
        return "errors"
    if slug.startswith("app-"):
        return "app-index"
    if "-changelist-" in slug:
        return "changelist-states"
    if slug.endswith("-changelist"):
        return "changelist"
    for kind in ("-add", "-change", "-delete", "-history"):
        if slug.endswith(kind):
            return kind[1:]
    return "changelist"


_GROUPS = [
    ("dashboard", "Dashboard"),
    ("changelist", "Changelist"),
    ("changelist-states", "Changelist states — search / pagination / date hierarchy"),
    ("add", "Add form"),
    ("change", "Change form"),
    ("stacked", "Change form — stacked (non-tabbed) layout"),
    ("delete", "Delete confirmation"),
    ("history", "History"),
    ("app-index", "App index"),
    ("interactions", "Select2 interactions"),
    ("auth-pages", "Login / password / logout"),
    ("errors", "Error pages (404 / 500 templates)"),
    ("dark", "Dark mode — main pages"),
]


def _write_review_index(run_dir: Path, manifest: list[dict], run: str):
    import html
    from collections import OrderedDict

    groups: dict[str, list] = OrderedDict((key, []) for key, _ in _GROUPS)
    for entry in manifest:
        groups.setdefault(_group_of(entry), []).append(entry)

    sections = []
    for key, title in _GROUPS:
        entries = groups.get(key)
        if not entries:
            continue
        figures = []
        for entry in entries:
            rel = Path(entry["file"]).relative_to(run_dir)
            warn = f" <span class='warn'>⚠ console: {html.escape('; '.join(entry['console_errors']))}</span>" if entry["console_errors"] else ""
            figures.append(
                "<figure>"
                f"<figcaption><code>{html.escape(entry['slug'])}</code>"
                f"<span class='meta'>{entry.get('status', '')} · {entry['bytes']:,} B</span>{warn}</figcaption>"
                f"<img loading=\"lazy\" src=\"{rel}\" alt=\"{html.escape(entry['slug'])}\" data-full=\"{rel}\" tabindex=\"0\">"
                "</figure>"
            )
        sections.append(
            f"<h2 id=\"{key}\">{title} <span class='meta'>({len(entries)})</span></h2>"
            f"<div class='grid'>{''.join(figures)}</div>"
        )

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
figure img {{ width: 100%; border: 1px solid #d1d5db; border-radius: 6px; background: #fff;
             cursor: zoom-in; }}
code {{ background: #eef2f7; padding: 0.05rem 0.3rem; border-radius: 4px; }}
#lightbox {{ display: none; position: fixed; inset: 0; z-index: 1000; background: rgba(15, 23, 42, .88);
             flex-direction: column; align-items: center; justify-content: center; gap: .75rem; }}
#lightbox.open {{ display: flex; }}
#lightbox img {{ max-width: 92vw; max-height: 84vh; border-radius: 8px; background: #fff; }}
#lightbox figcaption {{ color: #e5e7eb; font-family: monospace; font-size: .85rem; }}
#lightbox .nav {{ position: absolute; top: 50%; transform: translateY(-50%); font-size: 2rem;
                  color: #fff; background: rgba(255,255,255,.12); border: 0; border-radius: 8px;
                  width: 3rem; height: 4rem; cursor: pointer; line-height: 1; }}
#lightbox .nav:hover {{ background: rgba(255,255,255,.25); }}
#lightbox .prev {{ left: 1rem; }} #lightbox .next {{ right: 1rem; }}
#lightbox .close {{ position: absolute; top: 1rem; right: 1rem; font-size: 1.4rem; color: #fff;
                    background: none; border: 0; cursor: pointer; }}
</style></head><body>
<h1>django-jazzy-tabler — admin screenshot matrix</h1>
<p class="meta">Run: <strong>{html.escape(run)}</strong> · {len(manifest)} captures ·
desktop 1440×900 · click any image to browse with ‹ › arrows (← → and Esc work too) ·
generated by <code>tests/test_screenshots.py</code></p>
{''.join(sections)}
<div id="lightbox" role="dialog" aria-label="Screenshot gallery">
  <button class="close" aria-label="Close">✕</button>
  <button class="nav prev" aria-label="Previous">‹</button>
  <img alt="">
  <figcaption></figcaption>
  <button class="nav next" aria-label="Next">›</button>
</div>
<script>
(function () {{
  var imgs = Array.prototype.slice.call(document.querySelectorAll('.grid figure img'));
  var lb = document.getElementById('lightbox');
  var lbImg = lb.querySelector('img');
  var lbCap = lb.querySelector('figcaption');
  var i = 0;
  function show() {{
    lbImg.src = imgs[i].getAttribute('data-full');
    lbImg.alt = imgs[i].alt;
    lbCap.textContent = (i + 1) + ' / ' + imgs.length + ' — ' + imgs[i].alt;
  }}
  function open(n) {{ i = n; show(); lb.classList.add('open'); document.body.style.overflow = 'hidden'; }}
  function close() {{ lb.classList.remove('open'); document.body.style.overflow = ''; }}
  function nav(d) {{ i = (i + d + imgs.length) % imgs.length; show(); }}
  imgs.forEach(function (img, n) {{
    img.addEventListener('click', function () {{ open(n); }});
    img.addEventListener('keydown', function (e) {{ if (e.key === 'Enter') open(n); }});
  }});
  lb.querySelector('.prev').addEventListener('click', function (e) {{ e.stopPropagation(); nav(-1); }});
  lb.querySelector('.next').addEventListener('click', function (e) {{ e.stopPropagation(); nav(1); }});
  lb.querySelector('.close').addEventListener('click', close);
  lb.addEventListener('click', function (e) {{ if (e.target === lb) close(); }});
  document.addEventListener('keydown', function (e) {{
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') nav(-1);
    else if (e.key === 'ArrowRight') nav(1);
  }});
}})();
</script>
</body></html>"""
    (run_dir / "index.html").write_text(page)


def test_screenshot_matrix(demo_server, stacked_server, browser):
    run_dir = PROOFS_ROOT / RUN
    manifest: list[dict] = []
    inventory = [p for p in demo_server.inventory if p.get("screenshot", True) and _notable(p)]

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
        # full page: the point of the stacked variant is seeing fieldsets AND inlines
        _capture(page, tap, stacked_server.base_url, slug, url, name, 200, out_dir, manifest, "light", full_page=True)
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
