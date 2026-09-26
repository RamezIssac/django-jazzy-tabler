# Changelog

All notable changes to django-jazzy-tabler are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-09-27

### Changed

- **Tabler upgraded: 1.4.0 → 1.5.1** (bundled `vendor/tabler` assets; exact
  version recorded in `jazzy_tabler/static/vendor/tabler/VERSION`).
- `base.html` now follows the Tabler 1.5 navbar protocol
  (`<html data-bs-navbar-position="vertical">`, top header inside
  `.page-wrapper`) — without it, 1.5 hides the vertical sidebar whenever a
  horizontal navbar is present.
- FK related-object icons (add/change/view/delete next to FK widgets) are now
  inline FontAwesome glyphs colored with `currentColor` — correctly sized,
  vertically centred, and theme-aware in light **and** dark mode (previously
  hardcoded-color 24px `<img>` SVGs).
- select2 restyled in one CSS layer covering both the `default` theme
  (`JazzySelect`, changelist filters) and Django's `admin-autocomplete` theme
  (`autocomplete_fields`): input-matched height and border radius, primary
  focus ring, themed dropdown/search/choices in both color modes. No
  `!important`, no inline styles.

### Fixed

- Login form was missing the hidden `next` field — logging in from
  `/admin/login/` landed on `/accounts/profile/` (404) instead of the
  dashboard.

### Added

- Admin URL-coverage test suite: every inventoried admin URL (login, index,
  app indexes, per-model changelist/add/change/delete/history, plus
  searched/filtered/paginated/date-hierarchy states, 404/500 previews) is
  asserted to render. The inventory is derived from the registered admin site
  (`demo/admin_inventory.py`).
- Opt-in Playwright screenshot matrix (`JAZZY_SCREENSHOTS=1`): every
  inventoried URL captured at desktop viewport in light and dark into
  `proofs/<run>/`, with browser console errors gating the run.
- Computed-style layout tests for the theme chrome, FK icons and select2.
- Demo project: richer `blog` app (tags, authors, comments, M2M with
  `filter_horizontal`, stacked + tabular inlines, date hierarchy, filters,
  pagination) with deterministic seeding via `manage.py seed_demo`.
- Docs: rewritten README; full settings protocol reference in
  [docs/settings.md](docs/settings.md).
- `JAZZY_UI_TWEAKS["accent_color"]` is now actually applied (sidebar active
  item).

## [0.1.1] and earlier

Early alpha iterations; see the git history for details.
