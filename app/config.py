import logging
import os


logger = logging.getLogger(__name__)


def setup_logging():
    """Настраивает логирование: консоль + файл logs/wbm.log"""
    os.makedirs("logs", exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = logging.FileHandler("logs/wbm.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def get_timeout():
    """Читает WBM_TIMEOUT из окружения. Возвращает float."""
    raw = os.getenv("WBM_TIMEOUT", "5")
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"WBM_TIMEOUT must be a number, got: {raw!r}")


def get_interval():
    """
    Читает WBM_INTERVAL из окружения.
    Если не задан — возвращает None (одна проверка).
    """
    raw = os.getenv("WBM_INTERVAL")
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"WBM_INTERVAL must be a number, got: {raw!r}")
    if value <= 0:
        raise ValueError(f"WBM_INTERVAL must be positive, got: {value}")
    return value

def get_db_config():
    """
    Читает настройки PostgreSQL из окружения.
    Возвращает dict для psycopg_pool.AsyncConnectionPool.
    """
    return {
        "host": os.getenv("WBM_DB_HOST", "localhost"),
        "port": int(os.getenv("WBM_DB_PORT", "5432")),
        "dbname": os.getenv("WBM_DB_NAME", "wbm"),
        "user": os.getenv("WBM_DB_USER", "wbm"),
        "password": os.getenv("WBM_DB_PASSWORD", ""),
    }