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
- Browser pass (opt-in, Playwright): `uv sync --group screenshots && uv run playwright install chromium` once, then `JAZZY_SCREENSHOTS=1 uv run pytest`. It boots the seeded demo via `manage.py runserver` against a throwaway sqlite (`DEMO_DATABASE` env), captures every inventoried URL in light+dark into `proofs/<run>/` (name via `JAZZY_PROOFS_RUN`), and fails on browser console errors. Computed-style layout guards live in `tests/test_theme_layout.py` and `tests/test_widget_layout.py`.
- Never read/open screenshot PNGs into agent context; verify via file size + DOM assertions.
- Demo data: `uv run python manage.py migrate --run-syncdb && uv run python manage.py seed_demo --with-superuser` (admin / `$DEMO_ADMIN_PASSWORD`, default `admin`). `demo/seed.py` is shared by tests and the demo server.

## Upgrading the bundled Tabler

Vendor files live in `jazzy_tabler/static/vendor/tabler/` (version noted in its `VERSION` file). After swapping in new dist files, check Tabler's navbar protocol: 1.5+ requires `<html data-bs-navbar-position="vertical">` and the top header **inside** `.page-wrapper`, otherwise a direct-child `.navbar-vertical` sidebar is `display:none` when a horizontal navbar sibling exists. Verify with the browser pass above.

