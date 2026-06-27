import pytest

from demo.blog.models import Category, Post

pytest.importorskip("selenium")

from selenium import webdriver  # noqa: E402
from selenium.common.exceptions import WebDriverException  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402


@pytest.fixture
def chrome():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Chrome/chromedriver not available: {exc}")
    try:
        yield driver
    finally:
        driver.quit()


def _login(driver, base_url, username, password, next_url="/admin/"):
    driver.get(f"{base_url}/admin/login/?next={next_url}")
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type=submit], button[type=submit]").click()
    WebDriverWait(driver, 5).until(EC.url_contains(next_url))


@pytest.mark.django_db(transaction=True)
def test_empty_form_select_is_not_select2ified_and_survives_add(live_server, chrome, django_user_model):
    django_user_model.objects.create_superuser("jazzy", "s@s.com", "jazzypass")
    category = Category.objects.create(name="News")
    Post.objects.create(title="Hello", body="body", category=category, status="draft")

    _login(chrome, live_server.url, "jazzy", "jazzypass")
    chrome.get(f"{live_server.url}/admin/blog/category/{category.pk}/change/")
    WebDriverWait(chrome, 5).until(
        EC.presence_of_element_located((By.ID, "id_posts-0-status"))
    )
    chrome.execute_script("document.querySelector('[data-bs-target=\"#tab-posts\"]').click();")

    empty = chrome.execute_script("""
        var $ = window.jQuery;
        var sel = $('#posts-group .empty-form select').filter('[id*=__prefix__]');
        return {
            count: sel.length,
            has_select2: sel.hasClass('select2-hidden-accessible'),
            sibling_container: sel.nextAll('.select2-container').length,
        };
    """)
    assert empty["count"] == 1, empty
    assert empty["has_select2"] is False, "empty-form select must not be Select2-ified"
    assert empty["sibling_container"] == 0

    for _ in range(2):
        chrome.execute_script("document.querySelector('#posts-group .add-row a').click();")

    result = chrome.execute_script("""
        var $ = window.jQuery;
        var total = parseInt($('#id_posts-TOTAL_FORMS').val(), 10);
        var rows = [];
        for (var i = 0; i < total; i++) {
            var s = $('#id_posts-' + i + '-status');
            if (!s.length) continue;
            rows.push({
                idx: i,
                select2_init: s.hasClass('select2-hidden-accessible'),
                containers: s.nextAll('.select2-container').length,
            });
        }
        return {total: total, rows: rows};
    """)
    assert result["total"] == 4
    assert len(result["rows"]) == 4
    for row in result["rows"]:
        assert row["select2_init"] is True, row
        assert row["containers"] == 1, row
