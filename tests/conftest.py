import pytest
from fastapi.testclient import TestClient

from app.config import ROOT, Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path):
    s = Settings(database_path=str(tmp_path / "t.sqlite3"), content_dir=str(ROOT / "content"), facilitator_password="pw", reading_seconds=0, round_seconds=60)
    return s


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


FAC = {"X-Facilitator-Key": "pw"}
