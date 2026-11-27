"""The inline trash button checks DELETE, marks and hides the row, and fires a bubbling change event.

Part of the opt-in browser pass (JAZZY_SCREENSHOTS=1, see tests/test_screenshots.py).
"""

import pytest

from .conftest import fresh_context, login, requires_screenshots

pytestmark = [pytest.mark.screenshots, requires_screenshots]

# Listeners a consumer would bind: a django.jQuery delegate, a native listener, and a live-row total.
LISTEN_JS = """() => {
  window.seen = {jq: 0, native: 0, totals: []};
  const live = () => [...document.querySelectorAll('input[type=checkbox][name$="-DELETE"]')]
    .filter(cb => !cb.checked).length;
  django.jQuery(document).on('change', 'input[name$="-DELETE"]', () => { window.seen.jq++; });
  document.addEventListener('change', e => {
    if (e.target.name && e.target.name.endsWith('-DELETE')) { window.seen.native++; window.seen.totals.push(live()); }
  });
  return live();
}"""


@pytest.fixture(scope="module")
def page(demo_server, browser):
    context = fresh_context(browser, demo_server.base_url, "light")
    page = context.new_page()
    login(page, demo_server.base_url)
    yield page
    context.close()


@pytest.mark.parametrize(
    "url, tab, row_selector",
    [
        ("/admin/blog/category/1/change/", "#tab-posts", "tr.form-row.has_original"),
        ("/admin/blog/post/1/change/", "#tab-comments", "div.panel.inline-related.has_original"),
    ],
    ids=["tabular", "stacked"],
)
def test_trash_button_fires_change_and_marks_row(page, demo_server, url, tab, row_selector):
    page.goto(f"{demo_server.base_url}{url}", wait_until="networkidle")
    page.click(f'[data-bs-target="{tab}"]')
    live_before = page.evaluate(LISTEN_JS)
    row = page.locator(row_selector).first
    checkbox = row.locator('input[type=checkbox][name$="-DELETE"]')

    row.locator(".jazzy-delete-btn").click()

    assert checkbox.is_checked()
    assert row.is_hidden()
    assert "jazzy-deleted" in row.get_attribute("class")
    assert page.evaluate("window.seen") == {"jq": 1, "native": 1, "totals": [live_before - 1]}
