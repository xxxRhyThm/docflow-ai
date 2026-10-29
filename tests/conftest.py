import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCFLOW_DB_PATH", str(tmp_path / "test.db"))
    yield
    # database file is inside tmp_path and is cleaned up by pytest
