"""Browser-UI and accessibility guards: color-scheme meta, keyboard focus, accent colour, forced colours.

The meta checks run in the fast suite; the computed-style checks are part of the opt-in browser pass
(JAZZY_SCREENSHOTS=1, see tests/test_screenshots.py).
"""

import pytest

from .conftest import fresh_context, login, requires_screenshots

META = '<meta name="color-scheme" content="light dark">'

# WCAG contrast of an element's outline against its parent's composited background.
OUTLINE_CONTRAST_JS = """el => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 1;
  const cx = cv.getContext('2d', {willReadFrequently: true});
  const rgba = c => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1);
    const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const blend = (t, b) => [0, 1, 2].map(i => t[i] * t[3] + b[i] * (1 - t[3]));
  let bg = [255, 255, 255], layers = [];
  for (let e = el.parentElement; e; e = e.parentElement) {
    const c = rgba(getComputedStyle(e).backgroundColor); if (c[3] > 0) layers.push(c); if (c[3] >= 1) break; }
  for (let i = layers.length - 1; i >= 0; i--) bg = blend(layers[i], bg);
  const fg = blend(rgba(getComputedStyle(el).outlineColor), bg);
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const [a, b] = [lum(fg), lum(bg)].sort((x, y) => y - x);
  return (a + 0.05) / (b + 0.05);
}"""


@pytest.mark.django_db
@pytest.mark.parametrize("url", ["/admin/", "/admin/blog/post/", "/preview/404/", "/preview/500/"])
def test_color_scheme_meta_on_admin_pages(admin_client, url):
    content = admin_client.get(url).content.decode()

    assert META in content
    assert "querySelector('meta[name=color-scheme]').setAttribute('content', mode)" in content


@pytest.mark.django_db
def test_color_scheme_meta_on_login(client):
    content = client.get("/admin/login/").content.decode()

    assert META in content


@pytest.mark.parametrize("mode", ["light", "dark"])
@pytest.mark.screenshots
@requires_screenshots
def test_color_scheme_meta_follows_mode_and_toggle(demo_server, browser, mode):
    context = fresh_context(browser, demo_server.base_url, mode)
    page = context.new_page()
    login(page, demo_server.base_url)
    page.goto(f"{demo_server.base_url}/admin/", wait_until="networkidle")
    meta = "document.querySelector('meta[name=color-scheme]').getAttribute('content')"

    assert page.evaluate(meta) == mode
    page.click("#jazzy-mode-toggle")
    assert page.evaluate(meta) == ("light" if mode == "dark" else "dark")
    context.close()


@pytest.mark.parametrize("mode", ["light", "dark"])
@pytest.mark.parametrize("selector", ["#id_title", "input[name=_save]"])
@pytest.mark.screenshots
@requires_screenshots
def test_keyboard_focus_has_visible_outline(demo_server, browser, mode, selector):
    """Keyboard focus draws a solid outline of at least 2px and 3:1 contrast (WCAG 2.4.7, 1.4.11)."""
    context = fresh_context(browser, demo_server.base_url, mode)
    page = context.new_page()
    login(page, demo_server.base_url)
    page.goto(f"{demo_server.base_url}/admin/blog/post/add/", wait_until="networkidle")
    page.focus(selector)
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Tab")
    focused = page.locator(":focus")

    style = focused.evaluate("el => [getComputedStyle(el).outlineStyle, getComputedStyle(el).outlineWidth]")
    assert style[0] == "solid", f"{selector} focus outline is {style}"
    assert float(style[1].removesuffix("px")) >= 2
    assert focused.evaluate(OUTLINE_CONTRAST_JS) >= 3
    context.close()


@pytest.mark.parametrize("mode", ["light", "dark"])
@pytest.mark.screenshots
@requires_screenshots
def test_native_checkboxes_follow_theme_accent(demo_server, browser, mode):
    context = fresh_context(browser, demo_server.base_url, mode)
    page = context.new_page()
    login(page, demo_server.base_url)
    page.goto(f"{demo_server.base_url}/admin/blog/post/add/", wait_until="networkidle")

    accent, link = page.evaluate(
        """() => { const cb = document.querySelector('#id_is_featured'), probe = document.createElement('span');
          probe.style.color = 'var(--tblr-link-color)'; cb.parentElement.append(probe);
          const out = [getComputedStyle(cb).accentColor, getComputedStyle(probe).color]; probe.remove(); return out; }"""
    )
    assert accent != "auto"
    assert accent == link
    context.close()


@pytest.mark.screenshots
@requires_screenshots
def test_forced_colors_keep_boundaries(demo_server, browser):
    """In forced-colours mode cards keep a border and the active sidebar link keeps an outline."""
    context = fresh_context(browser, demo_server.base_url, "light")
    page = context.new_page()
    login(page, demo_server.base_url)
    page.emulate_media(forced_colors="active")
    page.goto(f"{demo_server.base_url}/admin/blog/post/", wait_until="networkidle")

    card = page.locator(".page-body .card").first.evaluate("el => getComputedStyle(el).borderTopStyle")
    active = page.locator("#jazzy-sidebar .dropdown-item.active, #jazzy-sidebar .nav-link.active").first
    assert card == "solid"
    assert active.evaluate("el => getComputedStyle(el).outlineStyle") == "solid"
    context.close()


@pytest.mark.screenshots
@requires_screenshots
def test_text_selection_uses_theme_tint(demo_server, browser):
    context = fresh_context(browser, demo_server.base_url, "light")
    page = context.new_page()
    login(page, demo_server.base_url)
    page.goto(f"{demo_server.base_url}/admin/", wait_until="networkidle")

    selection, tint = page.evaluate(
        """() => { const probe = document.createElement('span');
          probe.style.backgroundColor = 'color-mix(in oklab, var(--tblr-primary) 28%, transparent)'; document.body.append(probe);
          const out = [getComputedStyle(document.body, '::selection').backgroundColor, getComputedStyle(probe).backgroundColor];
          probe.remove(); return out; }"""
    )
    assert selection == tint
    context.close()
