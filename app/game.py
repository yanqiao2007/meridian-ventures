"""Session state machine for one committee (facilitator + up to four seats)."""
import random
import secrets
import time
from datetime import datetime, timezone

from . import rules
from .config import Settings
from .content import RoundContent, load_round
from .store import Store

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class GameError(Exception):
    pass


class Session:
    def __init__(self, code, store: Store, settings: Settings, state: dict = None, seed: int = None):
        self.code, self.store, self.settings = code, store, settings
        s = state or {}
        self.seed = s.get("seed", seed if seed is not None else secrets.randbits(32))
        self.round_no = s.get("round_no", 1)
        self.status = s.get("status", "lobby")          # lobby | running | frozen
        self.started_at = s.get("started_at")
        self.frozen_reason = s.get("frozen_reason")
        self.board = s.get("board", rules.new_board())
        self.seats = s.get("seats", None)                # role -> {"pid","token"} | None
        self.votes = s.get("votes", {})
        self.opened = s.get("opened", [])                # "pid:round" private pages already logged
        self.assignments = s.get("assignments", 0)
        self.content = load_round(settings.content_dir, self.round_no)
        if self.seats is None:
            self.seats = {r: None for r in self.content.roles}

    # ---- persistence / logging
    def to_state(self) -> dict:
        return {k: getattr(self, k) for k in ("seed", "round_no", "status", "started_at", "frozen_reason", "board", "seats", "votes", "opened", "assignments")}

    def save(self):
        self.store.save_session(self.code, self.to_state())

    def log(self, etype, actor=None, **kw):
        pid, role = (actor["pid"], actor["role"]) if actor else (None, None)
        self.store.add_event(self.code, now_iso(), self.round_no, pid, role, etype, **kw)

    # ---- timing
    def phase(self, now=None) -> str:
        if self.status != "running":
            return self.status
        el = (now or time.time()) - self.started_at
        return "reading" if el < self.settings.reading_seconds else "open"

    def remaining(self, now=None):
        if self.status != "running":
            return None
        return max(0.0, self.settings.round_seconds - ((now or time.time()) - self.started_at))

    def tick(self, now=None) -> bool:
        """Advance timed transitions. Returns True if state changed."""
        if self.status == "running" and self.remaining(now) <= 0:
            self.freeze("timer")
            return True
        return False

    # ---- players
    def actor(self, token):
        for role, seat in self.seats.items():
            if seat and seat["token"] == token:
                return {"role": role, "pid": seat["pid"]}
        return None

    def join(self) -> dict:
        vacant = [r for r, s in self.seats.items() if s is None]
        if not vacant:
            raise GameError("This session is full.")
        role = random.Random(f"{self.seed}:{self.assignments}").choice(sorted(vacant))
        self.assignments += 1
        seat = {"pid": "P" + secrets.token_hex(3).upper(), "token": secrets.token_urlsafe(16)}
        self.seats[role] = seat
        self.log("player_joined", {"pid": seat["pid"], "role": role})
        self.save()
        return {"token": seat["token"], "pid": seat["pid"], "role": role}

    def replace(self, role):
        if role not in self.seats or self.seats[role] is None:
            raise GameError("No participant in that role.")
        if self.status == "running":
            raise GameError("Participants can only be replaced between rounds.")
        old = self.seats[role]
        self.seats[role] = None
        self.votes.pop(old["pid"], None)
        self.log("player_removed", {"pid": old["pid"], "role": role}, detail={"role_history_kept": True})
        self.save()

    # ---- round control
    def start(self):
        if self.status != "lobby":
            raise GameError("Round already started.")
        if any(s is None for s in self.seats.values()):
            raise GameError("All four seats must be filled.")
        self.status, self.started_at = "running", time.time()
        self.log("round_started", detail={"reading_seconds": self.settings.reading_seconds, "round_seconds": self.settings.round_seconds, "seed": self.seed})
        self.save()

    def freeze(self, reason):
        if self.status != "running":
            raise GameError("Round is not running.")
        self.status, self.frozen_reason = "frozen", reason
        self.log("round_frozen", subject=reason)
        for cid, c in self.content.companies.items():
            self.log("final_board", subject=cid, field="row_chips_counters", after=f"{self.board['chips'].get(cid, 0)}|{self.board['counters'].get(cid, 0)}",
                     detail={"row": c["row"], "chips": self.board["chips"].get(cid, 0), "counters": self.board["counters"].get(cid, 0), "counter_type": rules.ROW_COUNTER[c["row"]]})
        self.log("final_board", subject="bank", field="chips", after=rules.bank(self.board, self.content))
        self.save()

    def advance(self):
        if self.status != "frozen":
            raise GameError("Freeze the current round first.")
        raise GameError("Advancing rounds needs the between-rounds outcome engine, which is not built yet (see docs/open_questions.md).")

    # ---- board actions
    def _require_open(self, actor):
        if not actor:
            raise GameError("Not seated.")
        self.tick()
        ph = self.phase()
        if ph == "reading":
            raise GameError("The board opens after the quiet reading period.")
        if ph != "open":
            raise GameError("The board is not open." if ph == "lobby" else "The board is frozen.")

    def set_funded(self, actor, cid, funded):
        self._require_open(actor)
        before = self.board["chips"].get(cid, 0)
        err = rules.set_funded(self.board, self.content, cid, bool(funded))
        if err:
            raise GameError(err)
        after = self.board["chips"].get(cid, 0)
        if before != after:
            self.log("board_change", actor, subject=cid, field="chips", before=before, after=after)
            self.votes.clear()
            self.save()
            return True
        return False

    def set_counters(self, actor, cid, n):
        self._require_open(actor)
        before = self.board["counters"].get(cid, 0)
        err = rules.set_counters(self.board, self.content, cid, n)
        if err:
            raise GameError(err)
        after = self.board["counters"].get(cid, 0)
        if before != after:
            kind = rules.ROW_COUNTER[self.content.companies[cid]["row"]]
            self.log("board_change", actor, subject=cid, field=f"{kind}_counters", before=before, after=after)
            self.votes.clear()
            self.save()
            return True
        return False

    def page_opened(self, actor):
        key = f"{actor['pid']}:{self.round_no}"
        if self.status == "lobby" or key in self.opened:
            return False
        self.opened.append(key)
        self.log("private_page_opened", actor)
        self.save()
        return True

    def early_finish(self, actor, agree: bool):
        self._require_open(actor)
        if self.votes.get(actor["pid"]) == agree:
            return
        self.votes[actor["pid"]] = agree
        self.log("early_finish_vote", actor, after=agree)
        if sum(1 for s in self.seats.values() if s and self.votes.get(s["pid"])) == len(self.seats):
            self.freeze("early_finish")
        self.save()

    # ---- views
    def public_state(self) -> dict:
        self.tick()
        c = self.content
        return {
            "code": self.code, "round": self.round_no, "status": self.status, "phase": self.phase(),
            "remaining": self.remaining(), "reading_seconds": self.settings.reading_seconds,
            "round_seconds": self.settings.round_seconds, "frozen_reason": self.frozen_reason,
            "board": self.board, "bank": rules.bank(self.board, c), "pool_left": rules.pool_left(self.board, c),
            "seats": {r: {"filled": s is not None, "pid": s["pid"] if s else None} for r, s in self.seats.items()},
            "early_finish_votes": sum(1 for s in self.seats.values() if s and self.votes.get(s["pid"])),
            "server_time": time.time(),
        }

    def view_for(self, actor) -> dict:
        v = {"state": self.public_state(), "content": self.content.public(), "you": actor}
        if actor and self.status != "lobby":
            v["private_page"] = self.content.private_page(actor["role"])
            v["you"]["voted_early"] = bool(self.votes.get(actor["pid"]))
        return v


class Manager:
    def __init__(self, store: Store, settings: Settings):
        self.store, self.settings = store, settings
        self.sessions = {c: Session(c, store, settings, state=s) for c, s in store.load_sessions().items()}

    def create(self, seed=None) -> Session:
        while True:
            code = "".join(random.SystemRandom().choice(CODE_ALPHABET) for _ in range(5))
            if code not in self.sessions:
                break
        s = Session(code, self.store, self.settings, seed=seed)
        self.sessions[code] = s
        s.log("session_created", detail={"seed": s.seed})
        s.save()
        return s

    def get(self, code):
        s = self.sessions.get(code.upper())
        if not s:
            raise GameError("Session not found.")
        return s
