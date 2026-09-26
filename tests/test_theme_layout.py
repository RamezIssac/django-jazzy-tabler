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
