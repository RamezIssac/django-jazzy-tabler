# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.

## Testing

- Fast suite (no browser): `uv sync && uv run pytest` — includes the admin URL-coverage suite (`tests/test_admin_urls.py`) driven by `demo/admin_inventory.py`, which derives every admin URL from the registered admin site. Extend the demo models/admins and the coverage follows automatically.
- Browser pass (opt-in, Playwright): `uv sync --group screenshots && uv run playwright install chromium` once, then `JAZZY_SCREENSHOTS=1 uv run pytest`. It boots the seeded demo via `manage.py runserver` against a throwaway sqlite (`DEMO_DATABASE` env) and captures the matrix into `proofs/<run>/` (name via `JAZZY_PROOFS_RUN`): light = full inventory (filter variants excluded — covered by the URL suite) + interaction shots + a stacked change-form variant (second server booted with `DEMO_CHANGEFORM_FORMAT=single`); dark = main pages only (index, changelist, change form). `proofs/<run>/index.html` is a grouped, deduplicated 4-column review grid with a lightbox gallery (groups keyed off the page slug; `_notable()` in `tests/test_screenshots.py` drops duplicate-perspective pages); browser console errors fail the run. Computed-style layout guards live in `tests/test_theme_layout.py` and `tests/test_widget_layout.py`.
- Never read/open screenshot PNGs into agent context; verify via file size + DOM assertions.
- Publish the matrix to GitHub Pages without CI: `scripts/publish-matrix-site.sh [--skip-capture] [--push]` (stages proofs into a gh-pages worktree; Pages source = gh-pages branch root).
- Release flow: PRs target `develop`; `main` is updated at release time (then tag + PyPI).
- Demo data: `uv run python manage.py migrate --run-syncdb && uv run python manage.py seed_demo --with-superuser` (admin / `$DEMO_ADMIN_PASSWORD`, default `admin`). `demo/seed.py` is shared by tests and the demo server.

## Upgrading the bundled Tabler

Vendor files live in `jazzy_tabler/static/vendor/tabler/` (version noted in its `VERSION` file). After swapping in new dist files, check Tabler's navbar protocol: 1.5+ requires `<html data-bs-navbar-position="vertical">` and the top header **inside** `.page-wrapper`, otherwise a direct-child `.navbar-vertical` sidebar is `display:none` when a horizontal navbar sibling exists. Verify with the browser pass above.

