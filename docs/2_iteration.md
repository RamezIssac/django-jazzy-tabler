# Iteration 2 — Core Admin Views

## Templates ported (11 new)

| Template | Purpose |
|---|---|
| `admin/index.html` | Dashboard — app cards + recent actions (Tabler list-group + avatar badges) |
| `admin/app_index.html` | App-specific dashboard |
| `admin/change_list.html` | Model list view — search, filters, results, pagination |
| `admin/change_list_results.html` | Results table (`table-vcenter table-striped card-table`) |
| `admin/change_form.html` | Model add/edit — fieldsets, inlines, submit row, actions sidebar |
| `admin/delete_confirmation.html` | Delete page (Tabler `card border-danger`) |
| `admin/object_history.html` | Change history (Tabler list-group timeline) |
| `admin/submit_line.html` | Save/Delete/Close buttons |
| `admin/search_form.html` | Standalone search + filters |
| `admin/filter.html` | Individual filter dropdown (`form-select`) |
| `admin/actions.html` | Bulk action bar |
| `admin/pagination.html` | Paginator controls |
| `admin/edit_inline/tabular.html` | Tabular inlines (`table-responsive table-vcenter`) |
| `admin/edit_inline/stacked.html` | Stacked inlines (Tabler cards with `border-success`/`border`) |

## JavaScript ported (2 new)

| File | Purpose |
|---|---|
| `change_list.js` | Select2 for filters, search filter binding |
| `change_form.js` | Tab/accordion handling, Select2 on forms, inline formset support |

## Template count

24 total (vs jazzmin's 73 — remaining are auth pages and third-party integrations for later iterations)
