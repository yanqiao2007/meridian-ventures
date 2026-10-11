"""Round content loaded from config files (content/round_N.json)."""
import json
import re
from pathlib import Path

ROW_COUNTER = {"owned": "support", "pipeline": "research", "scouting": "scout"}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class RoundContent:
    def __init__(self, raw: dict):
        self.raw = raw
        self.round = raw.get("round", 1)
        self.starting_chips = raw["currency"]["starting_chips"]
        self.owed = raw["currency"]["owed_next_round_chips"]
        self.pool = {k: raw["staff"][k]["count"] for k in ("support", "research", "scout")}
        self.max_per_company = raw["staff"]["max_counters_per_company"]
        self.roles = list(raw["private_pages"].keys())
        self.companies = {}
        for row in ("owned", "pipeline", "scouting"):
            for c in raw[row]:
                cid = slug(c["name"])
                cost = c.get("needs_chips") if row == "owned" else c.get("asking_high_musd") if row == "pipeline" else None
                self.companies[cid] = {
                    "id": cid, "name": c["name"], "line": c["line"], "summary": c["summary"], "row": row,
                    "cost": cost, "ask_low": c.get("asking_low_musd"), "ask_high": c.get("asking_high_musd"),
                    "est_profit": c.get("estimated_profit_musd"),
                }

    def public(self) -> dict:
        """Everything players may see. Reveal data and engine notes are never included."""
        r = self.raw
        return {
            "round": self.round, "starting_chips": self.starting_chips, "owed": self.owed,
            "pool": self.pool, "max_per_company": self.max_per_company,
            "companies": list(self.companies.values()), "rules": r["rules"],
            "mandate": r["mandate"], "profit_bands": r["profit_bands"], "roles": self.roles,
        }

    def private_page(self, role: str) -> list:
        return self.raw["private_pages"][role]


def load_round(content_dir: str, n: int):
    p = Path(content_dir) / f"round_{n}.json"
    if not p.exists():
        return None
    raw = json.loads(p.read_text())
    if raw.get("status") == "placeholder":
        return None
    return RoundContent(raw)
