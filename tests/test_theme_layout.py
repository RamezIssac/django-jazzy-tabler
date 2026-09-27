"""Computed-style layout guards for the theme chrome (browser pass, opt-in).

These assert the *structure* of the rendered pages — sidebar offset, tabs,
dark-mode application — so a Tabler upgrade that silently renames a class or
variable fails here even when every page still returns 200.

Run with JAZZY_SCREENSHOTS=1 (see tests/test_screenshots.py).
"""

import pytest

from .conftest import fresh_context, login, requires_screenshots

pytestmark = [pytest.mark.screenshots, requires_screenshots]


@pytest.fixture(scope="module")
def page(demo_server, browser):
    context = fresh_context(browser, demo_server.base_url, "light")
    page = context.new_page()
    login(page, demo_server.base_url)
    yield page
    context.close()


def _px(value: str) -> float:
    return float(value.replace("px", ""))


def test_sidebar_visible_and_offsets_content(page, demo_server):
    page.goto(f"{demo_server.base_url}/admin/", wait_until="networkidle")
    sidebar = page.locator("#jazzy-sidebar")
    box = sidebar.bounding_box()
    assert box is not None and box["width"] > 200, f"sidebar too narrow/missing: {box}"

    margin = page.evaluate("getComputedStyle(document.querySelector('.page-wrapper')).marginLeft")
    assert _px(margin) >= box["width"] - 1, f"page content not offset by sidebar (margin-left: {margin})"


def test_top_navbar_visible(page, demo_server):
    page.goto(f"{demo_server.base_url}/admin/", wait_until="networkidle")
    navbar = page.locator("header.navbar")
    assert navbar.is_visible()
    box = navbar.bounding_box()
    assert box is not None and box["height"] > 40


def test_dashboard_renders_app_cards(page, demo_server):
    page.goto(f"{demo_server.base_url}/admin/", wait_until="networkidle")
    assert page.locator(".card").count() >= 2, "dashboard should render app cards"
    assert page.locator("text=Blog").first.is_visible()
    assert page.locator("text=Authentication and Authorization").first.is_visible()


def test_changeform_tabs_render(page, demo_server):
    page.goto(f"{demo_server.base_url}/admin/blog/post/add/", wait_until="networkidle")
    tabs = page.locator("#content-main .nav-tabs").first
    assert tabs.is_visible(), "horizontal_tabs changeform format should render .nav-tabs"
    assert page.locator("#content-main .tab-pane.active").count() >= 1


def test_changelist_table_and_filters(page, demo_server):
    page.goto(f"{demo_server.base_url}/admin/blog/post/", wait_until="networkidle")
    rows = page.locator("#result_list tbody tr")
    assert rows.count() == 10, "PostAdmin.list_per_page = 10"  # noqa: PLR2004
    assert page.locator("#changelist-filter").count() >= 1 or page.locator(".filters, [id*=filter]").count() >= 1


def test_dark_theme_mode_applies(demo_server, browser):
    context = fresh_context(browser, demo_server.base_url, "dark")
    page = context.new_page()
    login(page, demo_server.base_url)
    page.goto(f"{demo_server.base_url}/admin/", wait_until="networkidle")

    assert page.evaluate("document.documentElement.getAttribute('data-bs-theme')") == "dark"
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    # dark background: every channel well below mid-grey
    channels = [int(c) for c in bg.removeprefix("rgb(").removeprefix("rgba(").removesuffix(")").split(",")][:3]
    assert all(c < 60 for c in channels), f"expected dark body background, got {bg}"
    context.close()


def test_light_theme_mode_applies(demo_server, browser):
    context = fresh_context(browser, demo_server.base_url, "light")
    page = context.new_page()
    login(page, demo_server.base_url)
    page.goto(f"{demo_server.base_url}/admin/", wait_until="networkidle")

    assert page.evaluate("document.documentElement.getAttribute('data-bs-theme')") == "light"
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    channels = [int(c) for c in bg.removeprefix("rgb(").removeprefix("rgba(").removesuffix(")").split(",")][:3]
    assert all(c > 200 for c in channels), f"expected light body background, got {bg}"
    context.close()


def test_page_title_groups_with_content(page, demo_server):
    """The page title must sit closer to its content than to the breadcrumbs."""
    page.goto(f"{demo_server.base_url}/admin/blog/post/", wait_until="networkidle")

    crumb = page.locator(".page-header .breadcrumb").first.bounding_box()
    title = page.locator(".page-header .page-title").bounding_box()
    body = page.locator(".page-body").bounding_box()
    assert crumb and title and body

    crumb_gap = title["y"] - (crumb["y"] + crumb["height"])
    content_gap = body["y"] - (title["y"] + title["height"])
    assert crumb_gap >= 6, f"title too close to breadcrumbs: {crumb_gap}px"
    assert content_gap <= 18, f"title too far from content: {content_gap}px"
    assert content_gap <= crumb_gap + 6, (
        f"title should group with content (crumb gap {crumb_gap}px, content gap {content_gap}px)"
    )


def test_submit_buttons_match_theme_button_family(page, demo_server):
    """Submit-row buttons and the changelist Add button must be one family."""
    page.goto(f"{demo_server.base_url}/admin/blog/post/1/change/", wait_until="networkidle")
    save = page.locator("input[name=_save]")
    save_h = save.bounding_box()["height"]
    save_fs = save.evaluate("el => getComputedStyle(el).fontSize")

    page.goto(f"{demo_server.base_url}/admin/blog/post/", wait_until="networkidle")
    add = page.locator(".page-header a[href$='/add/']").first
    add_h = add.bounding_box()["height"]
    add_fs = add.evaluate("el => getComputedStyle(el).fontSize")

    assert abs(save_h - add_h) < 2, f"save {save_h}px vs add {add_h}px"
    assert save_fs == add_fs, f"save font {save_fs} vs add font {add_fs}"


def test_changelist_search_row_items_aligned(page, demo_server):
    """Filter select2s, search input and Search button share one vertical center line."""
    page.goto(f"{demo_server.base_url}/admin/blog/post/", wait_until="networkidle")

    items = {
        "filter": page.locator("#changelist-search .form-group .select2-container").first,
        "input": page.locator("#changelist-search #searchbar"),
        "button": page.locator("#changelist-search button[type=submit]"),
    }
    centers = {}
    for name, locator in items.items():
        box = locator.bounding_box()
        assert box, f"{name} missing from search row"
        centers[name] = box["y"] + box["height"] / 2

    spread = max(centers.values()) - min(centers.values())
    assert spread <= 2, f"search row items off-center: {centers}"


def test_date_hierarchy_is_a_segmented_control(page, demo_server):
    page.goto(f"{demo_server.base_url}/admin/blog/post/", wait_until="networkidle")
    group = page.locator("#change-list-date-hierarchy .btn-group")
    assert group.is_visible()
    buttons = page.locator("#change-list-date-hierarchy .btn-group .btn")
    assert buttons.count() >= 2, "expected year choices"
    h = buttons.first.bounding_box()["height"]
    assert h < 36, f"date hierarchy buttons should be small, got {h}px"

    # drill to day level: the current choice is filled with the primary color
    page.goto(
        f"{demo_server.base_url}/admin/blog/post/?published_at__year=2024&published_at__month=1&published_at__day=15",
        wait_until="networkidle",
    )
    active = page.locator("#change-list-date-hierarchy .btn.active")
    assert active.count() == 1
    back = page.locator("#change-list-date-hierarchy .btn-outline-secondary")
    assert back.count() == 1, "expected a back link when drilled in"
    bg = active.first.evaluate("el => getComputedStyle(el).backgroundColor")
    channels = [round(float(c)) for c in bg[bg.index("(") + 1 : bg.rindex(")")].split(",")[:3]]
    assert not all(c > 200 for c in channels), f"active date choice not filled: {bg}"
