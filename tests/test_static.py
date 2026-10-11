import re
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_no_key_handler_property_assignments():
    """`el.onkeydown = e => cond && f()` returns false and cancels typing; use addEventListener."""
    for f in STATIC.iterdir():
        if f.suffix in (".js", ".html"):
            assert not re.search(r"\.on(keydown|keypress|keyup|beforeinput|input)\s*=", f.read_text()), f.name


def test_maxlength_only_on_session_code():
    fac = (STATIC / "facilitator.html").read_text()
    idx = (STATIC / "index.html").read_text()
    assert "maxlength" not in fac.lower()            # facilitator password: no length limit
    assert 'id="code"' in idx and 'maxlength="5"' in idx.split('id="code"')[1].split(">")[0]


def test_long_facilitator_password_in_browser(settings):
    import socket, threading, time

    import pytest
    uvicorn = pytest.importorskip("uvicorn")
    pw = pytest.importorskip("playwright.sync_api")
    from app.main import create_app
    settings.facilitator_password = "meridian123"
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    server = uvicorn.Server(uvicorn.Config(create_app(settings), port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    time.sleep(1.5)
    p = pw.sync_playwright().start()
    try:
        try:
            br = p.chromium.launch(channel="chrome")
        except Exception:
            pytest.skip("Chrome not available")
        page = br.new_page()
        page.goto(f"http://127.0.0.1:{port}/facilitator")
        page.click("#pw"); page.keyboard.type("meridian123")
        assert page.input_value("#pw") == "meridian123"
        page.keyboard.press("Enter")
        page.wait_for_selector("#top strong", timeout=5000)   # logged in, session created
        # the player code field still stops at 5 characters
        page.goto(f"http://127.0.0.1:{port}/")
        page.click("#code"); page.keyboard.type("meridian123")
        assert len(page.input_value("#code")) == 5
        br.close()
    finally:
        p.stop(); server.should_exit = True
