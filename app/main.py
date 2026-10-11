import asyncio
import csv
import hmac
import io
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .game import GameError, Manager
from .store import EVENT_COLS, Store

STATIC = Path(__file__).parent / "static"


def create_app(settings: Settings = None) -> FastAPI:
    settings = settings or Settings()
    store = Store(settings.database_path)
    mgr = Manager(store, settings)
    clients = {}   # code -> set of (ws, kind, token)

    async def broadcast(code):
        s = mgr.sessions[code]
        for ws, kind, token in list(clients.get(code, ())):
            try:
                if kind == "facilitator":
                    await ws.send_json({"type": "state", "state": s.public_state(), "content": s.content.public()})
                else:
                    await ws.send_json({"type": "state", **s.view_for(s.actor(token))})
            except Exception:
                clients[code].discard((ws, kind, token))

    async def ticker():
        last = {}
        while True:
            await asyncio.sleep(0.5)
            for code, s in list(mgr.sessions.items()):
                changed = s.tick()
                ph = s.phase()
                if changed or last.get(code, ph) != ph:
                    await broadcast(code)
                last[code] = ph

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(ticker())
        yield
        task.cancel()

    app = FastAPI(title="Meridian Ventures", lifespan=lifespan)
    app.state.settings, app.state.mgr = settings, mgr
    if settings.allowed_origins:
        app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_methods=["*"], allow_headers=["*"])

    def fac_ok(key):
        return bool(key) and hmac.compare_digest(key, settings.facilitator_password)

    def fac(key):
        if not fac_ok(key):
            raise HTTPException(401, "Bad facilitator password.")

    def session(code):
        try:
            return mgr.get(code)
        except GameError as e:
            raise HTTPException(404, str(e))

    async def run(code, fn, *a):
        try:
            r = fn(*a)
        except GameError as e:
            raise HTTPException(409, str(e))
        await broadcast(code)
        return r

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        return PlainTextResponse("", status_code=204)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    # ---- facilitator REST
    @app.post("/api/sessions")
    def create_session(seed: int = None, x_facilitator_key: str = Header(None)):
        fac(x_facilitator_key)
        s = mgr.create(seed)
        return {"code": s.code}

    @app.get("/api/sessions/{code}")
    def get_session(code: str, x_facilitator_key: str = Header(None)):
        fac(x_facilitator_key)
        return session(code).public_state()

    @app.post("/api/sessions/{code}/start")
    async def start(code: str, x_facilitator_key: str = Header(None)):
        fac(x_facilitator_key)
        return await run(code.upper(), session(code).start)

    @app.post("/api/sessions/{code}/freeze")
    async def freeze(code: str, x_facilitator_key: str = Header(None)):
        fac(x_facilitator_key)
        return await run(code.upper(), session(code).freeze, "facilitator")

    @app.post("/api/sessions/{code}/replace/{role}")
    async def replace(code: str, role: str, x_facilitator_key: str = Header(None)):
        fac(x_facilitator_key)
        return await run(code.upper(), session(code).replace, role)

    @app.post("/api/sessions/{code}/advance")
    async def advance(code: str, x_facilitator_key: str = Header(None)):
        fac(x_facilitator_key)
        return await run(code.upper(), session(code).advance)

    def csv_response(code, rows, name):
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(EVENT_COLS)
        w.writerows((r[0], i) + tuple(r[2:]) for i, r in enumerate(rows, 1))
        return PlainTextResponse(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{code}_{name}.csv"'})

    @app.get("/api/sessions/{code}/export/events.csv")
    def export_events(code: str, x_facilitator_key: str = Header(None)):
        fac(x_facilitator_key)
        s = session(code)
        return csv_response(s.code, store.events(s.code), "events")

    @app.get("/api/sessions/{code}/export/final_boards.csv")
    def export_final(code: str, x_facilitator_key: str = Header(None)):
        fac(x_facilitator_key)
        s = session(code)
        return csv_response(s.code, store.events(s.code, "final_board"), "final_boards")

    # ---- player REST + WS
    @app.post("/api/sessions/{code}/join")
    async def join(code: str):
        s = session(code)
        r = await run(s.code, s.join)
        return r

    @app.websocket("/ws/{code}")
    async def ws_endpoint(ws: WebSocket, code: str, token: str = "", key: str = ""):
        code = code.upper()
        s = mgr.sessions.get(code)
        is_fac = fac_ok(key)
        if not s or not (is_fac or s.actor(token)):
            await ws.close(code=4401)
            return
        await ws.accept()
        entry = (ws, "facilitator" if is_fac else "player", token)
        clients.setdefault(code, set()).add(entry)
        await broadcast(code)
        try:
            while True:
                msg = await ws.receive_json()
                if is_fac:
                    continue
                actor = s.actor(token)
                if not actor:
                    await ws.send_json({"type": "error", "message": "Your seat is no longer active."})
                    await ws.close(code=4401)
                    break
                try:
                    t = msg.get("type")
                    if t == "set_funded":
                        s.set_funded(actor, msg["company"], bool(msg["value"]))
                    elif t == "set_counters":
                        s.set_counters(actor, msg["company"], msg["value"])
                    elif t == "page_opened":
                        s.page_opened(actor)
                    elif t == "early_finish":
                        s.early_finish(actor, bool(msg["value"]))
                    else:
                        raise GameError("Unknown message.")
                except (GameError, KeyError) as e:
                    await ws.send_json({"type": "error", "message": str(e) if isinstance(e, GameError) else "Bad message."})
                    continue
                await broadcast(code)
        except WebSocketDisconnect:
            pass
        finally:
            clients.get(code, set()).discard(entry)

    # ---- pages
    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/facilitator")
    def facilitator_page():
        return FileResponse(STATIC / "facilitator.html")

    @app.get("/play")
    def play_page():
        return FileResponse(STATIC / "play.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
