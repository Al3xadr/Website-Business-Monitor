import pytest

from app.config import get_interval, get_timeout, get_db_config

def test_get_timeout_default(monkeypatch):
    monkeypatch.delenv("WBM_TIMEOUT", raising=False)
    assert get_timeout() == 5.0


def test_get_timeout_custom(monkeypatch):
    monkeypatch.setenv("WBM_TIMEOUT", "10")
    assert get_timeout() == 10.0


def test_get_timeout_float(monkeypatch):
    monkeypatch.setenv("WBM_TIMEOUT", "0.5")
    assert get_timeout() == 0.5


def test_get_timeout_invalid(monkeypatch):
    monkeypatch.setenv("WBM_TIMEOUT", "abc")
    with pytest.raises(ValueError):
        get_timeout()


def test_get_interval_default(monkeypatch):
    monkeypatch.delenv("WBM_INTERVAL", raising=False)
    assert get_interval() is None


def test_get_interval_custom(monkeypatch):
    monkeypatch.setenv("WBM_INTERVAL", "30")
    assert get_interval() == 30.0


def test_get_interval_invalid(monkeypatch):
    monkeypatch.setenv("WBM_INTERVAL", "abc")
    with pytest.raises(ValueError):
        get_interval()


def test_get_interval_negative(monkeypatch):
    monkeypatch.setenv("WBM_INTERVAL", "-5")
    with pytest.raises(ValueError):
        get_interval()


def test_get_interval_zero(monkeypatch):
    monkeypatch.setenv("WBM_INTERVAL", "0")
    with pytest.raises(ValueError):
        get_interval()

def test_get_db_config_defaults(monkeypatch):
    monkeypatch.delenv("WBM_DB_HOST", raising=False)
    monkeypatch.delenv("WBM_DB_PORT", raising=False)
    monkeypatch.delenv("WBM_DB_NAME", raising=False)
    monkeypatch.delenv("WBM_DB_USER", raising=False)
    monkeypatch.delenv("WBM_DB_PASSWORD", raising=False)

    cfg = get_db_config()

    assert cfg["host"] == "localhost"
    assert cfg["port"] == 5432
    assert cfg["dbname"] == "wbm"
    assert cfg["user"] == "wbm"
    assert cfg["password"] == ""


def test_get_db_config_custom(monkeypatch):
    monkeypatch.setenv("WBM_DB_HOST", "db.example.com")
    monkeypatch.setenv("WBM_DB_PORT", "5433")
    monkeypatch.setenv("WBM_DB_NAME", "mydb")
    monkeypatch.setenv("WBM_DB_USER", "alice")
    monkeypatch.setenv("WBM_DB_PASSWORD", "secret")

    cfg = get_db_config()

    assert cfg["host"] == "db.example.com"
    assert cfg["port"] == 5433          # int, не строка!
    assert cfg["dbname"] == "mydb"
    assert cfg["user"] == "alice"
    assert cfg["password"] == "secret"