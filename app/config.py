"""All deployment-sensitive settings come from environment variables."""
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent


def _int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


@dataclass
class Settings:
    host: str = field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _int("PORT", 8000))
    database_path: str = field(default_factory=lambda: os.environ.get("DATABASE_PATH", str(ROOT / "data" / "meridian.sqlite3")))
    content_dir: str = field(default_factory=lambda: os.environ.get("CONTENT_DIR", str(ROOT / "content")))
    round_seconds: int = field(default_factory=lambda: _int("ROUND_SECONDS", 1200))
    reading_seconds: int = field(default_factory=lambda: _int("READING_SECONDS", 180))
    allowed_origins: list = field(default_factory=lambda: [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()])
    facilitator_password: str = field(default_factory=lambda: os.environ.get("FACILITATOR_PASSWORD", ""))
    generated_password: bool = False

    def __post_init__(self):
        if not self.facilitator_password:
            self.facilitator_password = secrets.token_urlsafe(9)
            self.generated_password = True
