import pytest

from app import rules
from app.config import ROOT
from app.content import load_round


@pytest.fixture
def c():
    return load_round(str(ROOT / "content"), 1)


def test_content_loaded(c):
    assert c.starting_chips == 12 and c.pool == {"support": 3, "research": 3, "scout": 3}
    assert c.companies["nimbus-kitchens"]["cost"] == 5 and c.companies["solvanta"]["cost"] == 8
    assert c.companies["brightloom"]["cost"] == 2 and c.companies["kestrel-diagnostics"]["cost"] == 3
    assert c.roles == ["Sourcing", "Diligence", "Portfolio Management", "Fund Management"]


def test_public_content_hides_reveals(c):
    import json
    blob = json.dumps(c.public())
    assert "reveal_" not in blob and "engine_notes" not in blob and "Loss to Low" not in blob and "coded_facts" not in blob


def test_fund_exact_amounts_and_bank(c):
    b = rules.new_board()
    assert rules.set_funded(b, c, "solvanta", True) is None and b["chips"]["solvanta"] == 8
    assert rules.bank(b, c) == 4
    assert rules.set_funded(b, c, "nimbus-kitchens", True)  # 5 > 4 left
    assert rules.set_funded(b, c, "kestrel-diagnostics", True) is None
    assert rules.bank(b, c) == 1
    assert rules.set_funded(b, c, "brightloom", True)  # needs 2
    rules.set_funded(b, c, "solvanta", False)
    assert rules.bank(b, c) == 9


def test_funding_idempotent_no_overfund(c):
    b = rules.new_board()
    rules.set_funded(b, c, "brightloom", True)
    rules.set_funded(b, c, "brightloom", True)
    assert b["chips"]["brightloom"] == 2 and rules.bank(b, c) == 10


def test_no_chips_on_scouting(c):
    assert rules.set_funded(rules.new_board(), c, "quillmark", True)


def test_counter_limits(c):
    b = rules.new_board()
    assert rules.set_counters(b, c, "brightloom", 2) is None
    assert rules.set_counters(b, c, "brightloom", 3)          # max 2 per company
    assert rules.set_counters(b, c, "harbor-pine", 2)         # only 1 support left
    assert rules.set_counters(b, c, "harbor-pine", 1) is None
    assert rules.set_counters(b, c, "kestrel-diagnostics", 1)  # pool of 3 exhausted
    assert rules.pool_left(b, c) == {"support": 0, "research": 3, "scout": 3}
    assert rules.set_counters(b, c, "brightloom", 0) is None
    assert rules.pool_left(b, c)["support"] == 2


def test_counter_type_follows_row(c):
    b = rules.new_board()
    rules.set_counters(b, c, "quillmark", 2)
    rules.set_counters(b, c, "solvanta", 1)
    assert rules.pool_left(b, c) == {"support": 3, "research": 2, "scout": 1}


def test_invalid_inputs(c):
    b = rules.new_board()
    assert rules.set_counters(b, c, "brightloom", -1)
    assert rules.set_counters(b, c, "brightloom", True)
    assert rules.set_counters(b, c, "nope", 1)
