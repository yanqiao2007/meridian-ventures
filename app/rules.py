"""Pure rule enforcement for the shared board. No I/O.

Board = {"chips": {company_id: int}, "counters": {company_id: int}}
Counter type is fixed by the company's row (owned->support, pipeline->research, scouting->scout).
Operations are idempotent "set" operations so concurrent clicks from four devices converge.
"""
from .content import ROW_COUNTER, RoundContent


def new_board() -> dict:
    return {"chips": {}, "counters": {}}


def bank(board: dict, content: RoundContent) -> int:
    return content.starting_chips - sum(board["chips"].values())


def pool_left(board: dict, content: RoundContent) -> dict:
    used = {k: 0 for k in content.pool}
    for cid, n in board["counters"].items():
        used[ROW_COUNTER[content.companies[cid]["row"]]] += n
    return {k: content.pool[k] - used[k] for k in content.pool}


def set_funded(board: dict, content: RoundContent, cid: str, funded: bool):
    """Return (error|None). Mutates board on success."""
    c = content.companies.get(cid)
    if c is None:
        return "Unknown company."
    if c["row"] == "scouting":
        return "Scouting companies cannot take chips."
    cur = board["chips"].get(cid, 0)
    if funded:
        if cur:
            return None
        if bank(board, content) < c["cost"]:
            return f"Not enough chips in the bank ({bank(board, content)} left, {c['cost']} needed)."
        board["chips"][cid] = c["cost"]
    else:
        board["chips"].pop(cid, None)
    return None


def set_counters(board: dict, content: RoundContent, cid: str, n: int):
    c = content.companies.get(cid)
    if c is None:
        return "Unknown company."
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        return "Invalid counter count."
    if n > content.max_per_company:
        return f"At most {content.max_per_company} counters on one company."
    kind = ROW_COUNTER[c["row"]]
    cur = board["counters"].get(cid, 0)
    if n - cur > pool_left(board, content)[kind]:
        return f"No {kind} counters left."
    if n:
        board["counters"][cid] = n
    else:
        board["counters"].pop(cid, None)
    return None
