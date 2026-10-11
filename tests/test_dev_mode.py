import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import FAC


def test_dev_mode_off_by_default(client):
    assert client.get("/api/config").json() == {"development_mode": False}


def test_dev_mode_on(settings):
    settings.development_mode = True
    with TestClient(create_app(settings)) as c:
        assert c.get("/api/config").json() == {"development_mode": True}


def test_four_dev_identities_get_four_distinct_seats(settings):
    """Server side: four joins to one session give four distinct roles/tokens (dev ids live only in the browser)."""
    settings.development_mode = True
    with TestClient(create_app(settings)) as c:
        code = c.post("/api/sessions", headers=FAC).json()["code"]
        seats = [c.post(f"/api/sessions/{code}/join").json() for _ in range(4)]
        assert len({s["role"] for s in seats}) == 4 and len({s["token"] for s in seats}) == 4


def _browser():
    pw = pytest.importorskip("playwright.sync_api")
    p = pw.sync_playwright().start()
    try:
        return p, p.chromium.launch(channel="chrome")
    except Exception:
        p.stop()
        pytest.skip("Chrome not available")


@pytest.mark.parametrize("dev", [True, False])
def test_four_tabs_one_browser(settings, dev):
    import threading, time, socket, uvicorn
    settings.development_mode = dev
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    server = uvicorn.Server(uvicorn.Config(create_app(settings), port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    time.sleep(1.5)
    base = f"http://127.0.0.1:{port}"
    import httpx
    code = httpx.post(base + "/api/sessions", headers=FAC).json()["code"]
    p, br = _browser()
    try:
        ctx = br.new_context()   # ONE browser profile, shared localStorage
        roles = []
        for i in range(1, 5):
            pg = ctx.new_page()
            pg.goto(f"{base}/?dev_player=P{i}")
            pg.click("#code"); pg.keyboard.type(code); pg.keyboard.press("Enter")
            pg.wait_for_selector(".bar .pill")
            roles.append(pg.inner_text(".bar .pill:nth-of-type(2)"))
            pg.reload(); pg.wait_for_selector(".bar .pill")   # refresh restores the same seat
            assert pg.inner_text(".bar .pill:nth-of-type(2)") == roles[-1]
        if dev:
            assert len(set(roles)) == 4
        else:   # production flow: dev_player is ignored, one seat per device
            assert len(set(roles)) == 1
            assert "DEV" not in pg.inner_text(".bar")
    finally:
        br.close(); p.stop(); server.should_exit = True
