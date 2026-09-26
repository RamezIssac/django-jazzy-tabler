"""Computed-style verification for the Phase-3 polish fixes (browser pass).

FK related-object icons and select2 widgets are asserted by *measuring* the
rendered page (icon box vs input height, border radius equality, focus ring,
dropdown colors in light and dark) — never by looking at screenshots.

Run with JAZZY_SCREENSHOTS=1 (see tests/test_screenshots.py).
"""

import pytest

from .conftest import fresh_context, login, requires_screenshots

pytestmark = [pytest.mark.screenshots, requires_screenshots]

POST_ADD = "/admin/blog/post/add/"


@pytest.fixture(scope="module")
def page(demo_server, browser):
    context = fresh_context(browser, demo_server.base_url, "light")
    page = context.new_page()
    login(page, demo_server.base_url)
    yield page
    context.close()


def _px(value: str) -> float:
    return float(value.replace("px", ""))


def _channels(rgb: str) -> list[int]:
    inner = rgb[rgb.index("(") + 1 : rgb.rindex(")")]
    return [round(float(c)) for c in inner.split(",")[:3]]


def _css_var(page, name: str) -> str:
    """Resolve a CSS custom property to its computed color."""
    return page.evaluate(
        """name => {
            const d = document.createElement('div');
            d.style.backgroundColor = `var(${name})`;
            d.style.display = 'none';
            document.body.appendChild(d);
            const c = getComputedStyle(d).backgroundColor;
            d.remove();
            return c;
        }""",
        name,
    )


def test_fk_icons_proportioned_and_centered(page, demo_server):
    page.goto(f"{demo_server.base_url}{POST_ADD}", wait_until="networkidle")

    input_box = page.locator("#id_title").bounding_box()
    assert input_box, "plain text input missing"

    links = page.locator(".field-author .related-widget-wrapper-link")
    count = links.count()
    assert count >= 3, f"expected add/change/(delete/)view links, found {count}"

    for i in range(count):
        box = links.nth(i).bounding_box()
        assert box, "link not laid out"
        # link box matches the input height, within a pixel of rounding
        assert abs(box["height"] - input_box["height"]) < 2, (
            f"link {i} height {box['height']} vs input {input_box['height']}"
        )
        icon = links.nth(i).locator("i")
        ibox = icon.bounding_box()
        assert ibox, "icon glyph not laid out"
        # icon is small relative to the input (not the old 24px-in-38px look)
        assert 10 <= ibox["height"] <= 18, f"icon {i} height {ibox['height']}"
        assert 8 <= ibox["width"] <= 18, f"icon {i} width {ibox['width']}"
        # vertically and horizontally centred in its box
        icon_cy = ibox["y"] + ibox["height"] / 2
        link_cy = box["y"] + box["height"] / 2
        assert abs(icon_cy - link_cy) < 2, f"icon {i} off-centre by {abs(icon_cy - link_cy)}px"


def test_fk_icons_consistent_gap(page, demo_server):
    page.goto(f"{demo_server.base_url}{POST_ADD}", wait_until="networkidle")
    xs = page.locator(".field-author .related-widget-wrapper-link").evaluate_all(
        "els => els.map(e => ({x: e.getBoundingClientRect().x, w: e.getBoundingClientRect().width}))"
    )
    widths = {round(x["w"], 1) for x in xs}
    assert len(widths) == 1, f"inconsistent link widths: {widths}"


def test_fk_icons_theme_aware_in_both_modes(demo_server, browser):
    for mode in ("light", "dark"):
        context = fresh_context(browser, demo_server.base_url, mode)
        page = context.new_page()
        login(page, demo_server.base_url)
        page.goto(f"{demo_server.base_url}{POST_ADD}", wait_until="networkidle")
        color = page.locator(".field-author .related-widget-wrapper-link").first.evaluate(
            "el => getComputedStyle(el).color"
        )
        channels = _channels(color)
        if mode == "dark":
            assert all(c > 100 for c in channels), f"dark mode icons too dark: {color}"
        else:
            assert all(c < 200 for c in channels), f"light mode icons too light: {color}"
        context.close()


def test_select2_matches_input_metrics(page, demo_server):
    """Both select2 themes (default + admin-autocomplete) match input geometry."""
    page.goto(f"{demo_server.base_url}{POST_ADD}", wait_until="networkidle")

    input_el = page.locator("#id_title")
    input_box = input_el.bounding_box()
    input_radius = input_el.evaluate("el => getComputedStyle(el).borderTopLeftRadius")

    for scope, theme in ((".field-author", "default"), (".field-category", "admin-autocomplete")):
        container = page.locator(f"{scope} .select2-container")
        assert container.count() == 1, f"{theme}: select2 not initialised in {scope}"
        selection = page.locator(f"{scope} .select2-container .select2-selection--single")
        box = selection.bounding_box()
        assert box, f"{theme}: selection not laid out"
        assert abs(box["height"] - input_box["height"]) < 2, (
            f"{theme}: select2 height {box['height']} vs input {input_box['height']}"
        )
        radius = selection.evaluate("el => getComputedStyle(el).borderTopLeftRadius")
        assert radius == input_radius, f"{theme}: radius {radius} != input {input_radius}"
        # no double border: the container itself must stay borderless
        border = container.evaluate("el => getComputedStyle(el).borderTopWidth")
        assert _px(border) == 0, f"{theme}: container border {border}"


def test_select2_focus_ring_and_dropdown_colors(page, demo_server):
    page.goto(f"{demo_server.base_url}{POST_ADD}", wait_until="networkidle")

    page.locator(".field-author .select2-selection--single").click()
    page.wait_for_selector(".select2-container--open")

    shadow = page.locator(".field-author .select2-selection--single").evaluate(
        "el => getComputedStyle(el).boxShadow"
    )
    assert shadow != "none", "focus ring missing on open select2"

    dropdown = page.locator(".select2-dropdown")
    assert dropdown.is_visible()
    surface = _css_var(page, "--tblr-bg-surface")
    dd_bg = dropdown.evaluate("el => getComputedStyle(el).backgroundColor")
    assert dd_bg == surface, f"dropdown bg {dd_bg} != --tblr-bg-surface {surface}"

    primary = _css_var(page, "--tblr-primary")
    highlighted = page.locator(".select2-results__option--highlighted").first
    hl_bg = highlighted.evaluate("el => getComputedStyle(el).backgroundColor")
    assert hl_bg == primary, f"highlighted option bg {hl_bg} != --tblr-primary {primary}"


def test_select2_dark_mode_colors(demo_server, browser):
    context = fresh_context(browser, demo_server.base_url, "dark")
    page = context.new_page()
    login(page, demo_server.base_url)
    page.goto(f"{demo_server.base_url}{POST_ADD}", wait_until="networkidle")

    selection = page.locator(".field-author .select2-selection--single")
    bg = selection.evaluate("el => getComputedStyle(el).backgroundColor")
    color = selection.evaluate("el => getComputedStyle(el).color")
    assert all(c < 80 for c in _channels(bg)), f"dark select2 selection bg too bright: {bg}"
    assert all(c > 150 for c in _channels(color)), f"dark select2 text too dark: {color}"

    selection.click()
    page.wait_for_selector(".select2-container--open")
    dd_bg = page.locator(".select2-dropdown").evaluate("el => getComputedStyle(el).backgroundColor")
    assert all(c < 80 for c in _channels(dd_bg)), f"dark dropdown bg too bright: {dd_bg}"
    context.close()


def test_inline_empty_form_not_select2ified_and_added_rows_are(page, demo_server):
    """Tabular inline: the hidden __prefix__ template form must stay a plain
    <select>, while rows added via 'Add another' get select2 exactly once.
    (Ported from the old selenium test — the live_server + in-memory sqlite
    combination raced and flaked; the seeded demo server is deterministic.)"""
    page.goto(f"{demo_server.base_url}/admin/blog/category/1/change/", wait_until="networkidle")
    page.click('[data-bs-target="#tab-posts"]')

    empty = page.evaluate(
        """() => {
            const sel = document.querySelector('#posts-group .empty-form select[id*=__prefix__]');
            if (!sel) return {count: 0};
            return {
                count: 1,
                has_select2: sel.classList.contains('select2-hidden-accessible'),
                sibling_container: sel.parentElement.querySelectorAll('.select2-container').length,
            };
        }"""
    )
    assert empty["count"] == 1, empty
    assert empty["has_select2"] is False, "empty-form select must not be Select2-ified"
    assert empty["sibling_container"] == 0, "empty-form select must have no select2 container"

    initial_total = int(page.locator("#id_posts-TOTAL_FORMS").input_value())

    page.locator("#posts-group .add-row a").click()
    page.locator("#posts-group .add-row a").click()

    result = page.evaluate(
        """() => {
            const total = parseInt(document.querySelector('#id_posts-TOTAL_FORMS').value, 10);
            const rows = [];
            for (let i = 0; i < total; i++) {
                const s = document.querySelector('#id_posts-' + i + '-status');
                if (!s) continue;
                rows.push({
                    idx: i,
                    select2_init: s.classList.contains('select2-hidden-accessible'),
                    containers: s.parentElement.querySelectorAll('.select2-container').length,
                });
            }
            return {total, rows};
        }"""
    )
    assert result["total"] == initial_total + 2, result
    assert len(result["rows"]) == result["total"], result
    for row in result["rows"]:
        assert row["select2_init"] is True, row
        assert row["containers"] == 1, row
