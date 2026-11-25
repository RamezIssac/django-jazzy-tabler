"""Skins: the `skin` UI tweak, the skin stylesheet hook in the page head, and the skin chooser menu."""

import logging
import re
from pathlib import Path

import pytest

from jazzy_tabler.settings import SKINS, get_ui_tweaks

from .conftest import fresh_context, login, requires_screenshots

STATIC = Path(__file__).resolve().parent.parent / "jazzy_tabler" / "static"
SKIN_DIR = STATIC / "jazzy_tabler" / "css" / "skins"
PAGES = ["/admin/", "/admin/blog/post/", "/preview/404/", "/preview/500/"]


def test_skin_list_matches_the_stylesheets_on_disk():
    assert set(SKINS) == {path.stem for path in SKIN_DIR.glob("*.css")}


@pytest.mark.parametrize("name", SKINS)
def test_skin_stylesheet_is_scoped_and_its_fonts_exist(name):
    css = (SKIN_DIR / f"{name}.css").read_text()

    assert f'[data-jazzy-skin="{name}"]' in css
    for url in re.findall(r'url\("([^"]+)"\)', css):
        assert (SKIN_DIR / url).resolve().is_file(), url


def test_unknown_skin_falls_back_to_stock_with_a_warning(settings, caplog):
    settings.JAZZY_UI_TWEAKS = {"skin": "bebop"}

    with caplog.at_level(logging.WARNING, logger="jazzy_tabler.settings"):
        tweaks = get_ui_tweaks()

    assert tweaks["skin"] is None
    assert tweaks["skin_href"] is None
    assert "skin must be one of" in caplog.text


@pytest.mark.django_db
@pytest.mark.parametrize("url", PAGES)
def test_no_skin_and_no_chooser_render_neither_attribute_nor_link(admin_client, settings, url):
    settings.JAZZY_UI_TWEAKS = {}
    content = admin_client.get(url).content.decode()

    assert "data-jazzy-skin" not in content
    assert "jazzy-skin-css" not in content
    assert "jazzy-skin-chooser" not in content


@pytest.mark.django_db
@pytest.mark.parametrize("url", PAGES)
def test_configured_skin_sets_attribute_and_stylesheet(admin_client, settings, url):
    settings.JAZZY_UI_TWEAKS = {"skin": "sus4"}
    content = admin_client.get(url).content.decode()

    assert '<html lang="en' in content and 'data-jazzy-skin="sus4"' in content
    assert 'id="jazzy-skin-css" href="/static/jazzy_tabler/css/skins/sus4.css"' in content
    assert content.index("jazzy_tabler/css/main.css") < content.index("skins/sus4.css")


@pytest.mark.django_db
def test_configured_skin_applies_to_the_login_page(client, settings):
    settings.JAZZY_UI_TWEAKS = {"skin": "tritone"}
    content = client.get("/admin/login/").content.decode()

    assert 'data-jazzy-skin="tritone"' in content
    assert "skins/tritone.css" in content


@pytest.mark.django_db
def test_chooser_lists_stock_and_every_skin(admin_client, settings):
    settings.JAZZY_UI_TWEAKS = {"skin_chooser": True}
    content = admin_client.get("/admin/").content.decode()

    assert 'id="jazzy-skin-chooser"' in content
    assert 'data-jazzy-skin-choice=""' in content
    for name in SKINS:
        assert f'data-jazzy-skin-choice="{name}"' in content
        assert f'"{name}": "/static/jazzy_tabler/css/skins/{name}.css"' in content
    # No configured skin: the link is present for the chooser but loads nothing.
    assert '<link rel="stylesheet" id="jazzy-skin-css">' in content
    assert content.index("jazzy-skin-chooser") < content.index("jazzy-mode-toggle")


@pytest.mark.django_db
def test_chooser_keeps_the_configured_skin_as_default(admin_client, settings):
    settings.JAZZY_UI_TWEAKS = {"skin_chooser": True, "skin": "minor"}
    content = admin_client.get("/admin/").content.decode()

    assert 'data-jazzy-skin="minor"' in content
    assert 'id="jazzy-skin-css" href="/static/jazzy_tabler/css/skins/minor.css"' in content


@pytest.mark.screenshots
@requires_screenshots
def test_chooser_switches_and_remembers_the_skin(demo_server, browser):
    context = fresh_context(browser, demo_server.base_url, "light")
    page = context.new_page()
    login(page, demo_server.base_url)
    page.goto(f"{demo_server.base_url}/admin/", wait_until="networkidle")
    skin = "document.documentElement.getAttribute('data-jazzy-skin')"
    href = "document.getElementById('jazzy-skin-css').getAttribute('href')"

    page.click("#jazzy-skin-chooser > a")
    page.click('[data-jazzy-skin-choice="sus4"]')
    assert page.evaluate(skin) == "sus4"
    assert page.evaluate(href).endswith("skins/sus4.css")
    # The swapped stylesheet loads asynchronously; its font stack proves it applied.
    page.wait_for_function("getComputedStyle(document.body).fontFamily.startsWith('\"Jazzy Inter\"')", timeout=5000)

    page.reload(wait_until="networkidle")
    assert page.evaluate(skin) == "sus4"
    assert page.get_attribute('[data-jazzy-skin-choice="sus4"]', "aria-pressed") == "true"

    page.click("#jazzy-skin-chooser > a")
    page.click('[data-jazzy-skin-choice=""]')
    assert page.evaluate(skin) is None
    assert page.evaluate(href) is None

    page.evaluate("localStorage.setItem('jazzy-skin', 'not-a-skin')")
    page.reload(wait_until="networkidle")
    assert page.evaluate(skin) is None
    context.close()
