from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# Must be set before any test module imports stallpay.config.
os.environ["STALLPAY_FORCE_HEURISTIC"] = "1"
os.environ.setdefault("PAYPAL_MODE", "mock")
os.environ.setdefault("PUBLIC_BASE_URL", "http://testserver")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def tmp_db_path(tmp_path_factory):
    return tmp_path_factory.mktemp("stallpay") / "test.db"


@pytest.fixture(scope="session", autouse=True)
def configure_env(tmp_db_path):
    os.environ["DATABASE_PATH"] = str(tmp_db_path)
    os.environ["PAYPAL_MODE"] = "mock"
    os.environ["PUBLIC_BASE_URL"] = "http://testserver"
    os.environ["STALLPAY_FORCE_HEURISTIC"] = "1"
    # Re-import config values after env is set if modules were already imported.
    from stallpay import config

    config.DATABASE_PATH = tmp_db_path
    config.PAYPAL_MODE = "mock"
    config.PUBLIC_BASE_URL = "http://testserver"
    config.FORCE_HEURISTIC = True
    config.LLM_AVAILABLE = False
    yield


@pytest.fixture()
def client(configure_env):
    from stallpay.paypal import mock as mock_mod
    from stallpay.main import app
    from stallpay import db
    from fastapi.testclient import TestClient

    mock_mod.reset_store()
    if Path(os.environ["DATABASE_PATH"]).exists():
        Path(os.environ["DATABASE_PATH"]).unlink()
    db._initialized = False
    db.init_db()
    with TestClient(app) as test_client:
        yield test_client
