import re
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_no_key_handler_property_assignments():
    """`el.onkeydown = e => cond && f()` returns false and cancels typing; use addEventListener."""
    for f in STATIC.iterdir():
        if f.suffix in (".js", ".html"):
            assert not re.search(r"\.on(keydown|keypress|keyup|beforeinput|input)\s*=", f.read_text()), f.name
