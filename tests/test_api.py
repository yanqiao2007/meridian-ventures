import pytest

from tests.conftest import FAC


def make_session(client, seed=7):
    code = client.post(f"/api/sessions?seed={seed}", headers=FAC).json()["code"]
    players = [client.post(f"/api/sessions/{code}/join").json() for _ in range(4)]
    return code, players


def test_facilitator_auth(client):
    assert client.post("/api/sessions").status_code == 401
    assert client.post("/api/sessions", headers={"X-Facilitator-Key": "x"}).status_code == 401


def test_roles_unique_and_fifth_rejected(client):
    code, players = make_session(client)
    assert sorted(p["role"] for p in players) == ["Diligence", "Fund Management", "Portfolio Management", "Sourcing"]
    assert client.post(f"/api/sessions/{code}/join").status_code == 409


def test_role_assignment_reproducible_by_seed(client):
    a = [p["role"] for p in make_session(client, 99)[1]]
    b = [p["role"] for p in make_session(client, 99)[1]]
    assert a == b


def test_cannot_start_until_full(client):
    code = client.post("/api/sessions", headers=FAC).json()["code"]
    client.post(f"/api/sessions/{code}/join")
    assert client.post(f"/api/sessions/{code}/start", headers=FAC).status_code == 409


def test_bad_ws_token_rejected(client):
    code, _ = make_session(client)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/{code}?token=bogus"):
            pass


def test_full_round_flow(client):
    code, players = make_session(client)
    a, b = players[0], players[1]
    with client.websocket_connect(f"/ws/{code}?token={a['token']}") as wa, client.websocket_connect(f"/ws/{code}?token={b['token']}") as wb:
        wa.receive_json(); wa.receive_json(); m = wb.receive_json()   # wa also sees wb joining
        assert m["state"]["status"] == "lobby" and "private_page" not in m
        assert client.post(f"/api/sessions/{code}/start", headers=FAC).status_code == 200
        wa.receive_json(); m = wb.receive_json()
        assert m["state"]["phase"] == "open" and m["private_page"]  # reading_seconds=0 in tests
        # b's view never contains a's private page
        assert m["you"]["role"] == b["role"]

        wa.send_json({"type": "page_opened"}); wa.receive_json(); wb.receive_json()
        wa.send_json({"type": "set_funded", "company": "harbor-pine", "value": True})
        assert wa.receive_json()["state"]["bank"] == 10
        assert wb.receive_json()["state"]["board"]["chips"] == {"harbor-pine": 2}   # real-time to other device
        wb.send_json({"type": "set_funded", "company": "quillmark", "value": True})
        assert wb.receive_json()["type"] == "error"
        wb.send_json({"type": "set_counters", "company": "brightloom", "value": 3})
        assert wb.receive_json()["type"] == "error"
        wb.send_json({"type": "set_counters", "company": "quillmark", "value": 2})
        s = wb.receive_json()["state"]; wa.receive_json()
        assert s["pool_left"]["scout"] == 1

        assert client.post(f"/api/sessions/{code}/freeze", headers=FAC).status_code == 200
        assert wa.receive_json()["state"]["status"] == "frozen"; wb.receive_json()
        wa.send_json({"type": "set_funded", "company": "brightloom", "value": True})
        assert "frozen" in wa.receive_json()["message"]

    ev = client.get(f"/api/sessions/{code}/export/events.csv", headers=FAC).text
    lines = ev.strip().splitlines()
    assert lines[0].startswith("session_code,seq,ts_utc,round,participant_id,role,event_type")
    types = [l.split(",")[6] for l in lines[1:]]
    for t in ("session_created", "player_joined", "round_started", "private_page_opened", "board_change", "round_frozen", "final_board"):
        assert t in types
    assert types.count("private_page_opened") == 1   # first open only
    fb = client.get(f"/api/sessions/{code}/export/final_boards.csv", headers=FAC).text
    assert "harbor-pine" in fb and "bank" in fb


def test_early_finish_requires_all_four_and_resets_on_change(client):
    code, players = make_session(client)
    client.post(f"/api/sessions/{code}/start", headers=FAC)
    conns = [client.websocket_connect(f"/ws/{code}?token={p['token']}") for p in players]
    wss = [c.__enter__() for c in conns]
    try:
        for w in wss: w.receive_json()
        for w in wss[:3]:
            w.send_json({"type": "early_finish", "value": True})
        s = client.get(f"/api/sessions/{code}", headers=FAC).json()
        assert s["status"] == "running" and s["early_finish_votes"] == 3
        wss[3].send_json({"type": "set_funded", "company": "brightloom", "value": True})
        import time; time.sleep(0.2)
        assert client.get(f"/api/sessions/{code}", headers=FAC).json()["early_finish_votes"] == 0
        for w in wss:
            w.send_json({"type": "early_finish", "value": True})
        time.sleep(0.3)
        s = client.get(f"/api/sessions/{code}", headers=FAC).json()
        assert s["status"] == "frozen" and s["frozen_reason"] == "early_finish"
    finally:
        for c in conns: c.__exit__(None, None, None)


def test_replace_between_rounds_only_and_keeps_history(client):
    code, players = make_session(client)
    client.post(f"/api/sessions/{code}/start", headers=FAC)
    assert client.post(f"/api/sessions/{code}/replace/Sourcing", headers=FAC).status_code == 409
    client.post(f"/api/sessions/{code}/freeze", headers=FAC)
    old = next(p for p in players if p["role"] == "Sourcing")
    assert client.post(f"/api/sessions/{code}/replace/Sourcing", headers=FAC).status_code == 200
    new = client.post(f"/api/sessions/{code}/join").json()
    assert new["role"] == "Sourcing" and new["pid"] != old["pid"]
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/{code}?token={old['token']}"):
            pass
    ev = client.get(f"/api/sessions/{code}/export/events.csv", headers=FAC).text
    assert "player_removed" in ev and old["pid"] in ev and new["pid"] in ev


def test_timer_freezes_round(settings):
    from fastapi.testclient import TestClient
    from app.main import create_app
    import time
    settings.round_seconds = 1
    with TestClient(create_app(settings)) as c:
        code, _ = make_session(c)
        c.post(f"/api/sessions/{code}/start", headers=FAC)
        time.sleep(1.8)
        s = c.get(f"/api/sessions/{code}", headers=FAC).json()
        assert s["status"] == "frozen" and s["frozen_reason"] == "timer"


def test_sessions_survive_restart(settings):
    from fastapi.testclient import TestClient
    from app.main import create_app
    with TestClient(create_app(settings)) as c:
        code, _ = make_session(c)
        c.post(f"/api/sessions/{code}/start", headers=FAC)
    with TestClient(create_app(settings)) as c2:
        assert c2.get(f"/api/sessions/{code}", headers=FAC).json()["status"] == "running"
