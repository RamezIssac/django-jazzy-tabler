import os
from types import SimpleNamespace

import pytest

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "jazzy-screenshots-pw"
VIEWPORT = {"width": 1440, "height": 900}

SCREENSHOTS_ENABLED = os.environ.get("JAZZY_SCREENSHOTS") == "1"
requires_screenshots = pytest.mark.skipif(
    not SCREENSHOTS_ENABLED,
    reason="browser pass is opt-in: set JAZZY_SCREENSHOTS=1 (needs the 'screenshots' dependency group)",
)


@pytest.fixture()
def seeded(db):
    """Fresh database populated with the deterministic demo dataset."""
    from demo.seed import seed

    return seed()


@pytest.fixture(scope="session")
def demo_server(tmp_path_factory):
    """The seeded demo project served by a real ``manage.py runserver`` subprocess.

    A real server (not the test client) so CSS/JS are served exactly as in the demo.
    """
    if not SCREENSHOTS_ENABLED:
        pytest.skip("browser pass is opt-in: set JAZZY_SCREENSHOTS=1")

    import json
    import socket
    import subprocess
    import sys
    import time
    import urllib.request
    from pathlib import Path

    workdir = Path(__file__).resolve().parent.parent
    tmp = tmp_path_factory.mktemp("jazzy-screenshots")
    db_path = tmp / "demo.sqlite3"
    log_path = tmp / "runserver.log"

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    env = {
        **os.environ,
        "DEMO_DATABASE": str(db_path),
        "DEMO_ADMIN_PASSWORD": ADMIN_PASSWORD,
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    def manage(*args: str) -> str:
        result = subprocess.run(
            [sys.executable, "manage.py", *args],
            cwd=workdir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    manage("migrate", "--run-syncdb", "-v0")
    manage("seed_demo", "--with-superuser", "-v0")
    inventory = json.loads(manage("dump_admin_inventory"))

    log = open(log_path, "w")  # noqa: SIM115 - closed in fixture teardown
    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=workdir,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 60
    while True:
        try:
            urllib.request.urlopen(f"{base_url}/admin/login/", timeout=1)
            break
        except Exception:
            if proc.poll() is not None or time.time() > deadline:
                log.close()
                proc.kill()
                raise RuntimeError(f"demo server did not start; see {log_path}")
            time.sleep(0.25)

    yield SimpleNamespace(base_url=base_url, inventory=inventory, log_path=log_path)

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    log.close()


@pytest.fixture(scope="session")
def browser(demo_server):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


def fresh_context(browser, base_url: str, theme_mode: str):
    """Browser context pinned to a theme mode (the theme reads localStorage at first paint)."""
    context = browser.new_context(viewport=VIEWPORT)
    context.add_init_script(f"localStorage.setItem('jazzy-theme-mode', '{theme_mode}');")
    return context


def login(page, base_url: str):
    page.goto(f"{base_url}/admin/login/")
    page.fill("#id_username", ADMIN_USERNAME)
    page.fill("#id_password", ADMIN_PASSWORD)
    page.click("button[type=submit]")
    page.wait_for_url("**/admin/")
