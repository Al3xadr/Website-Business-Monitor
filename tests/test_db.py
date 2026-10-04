from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db import Database


# ─── Вспомогательная функция ────────────────────────────────────────────

def make_async_cm(return_value):
    """
    Возвращает объект, который ведёт себя как `async with X as y`.
    `y` будет равно return_value.
    """
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=return_value)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


def make_fake_pool():
    """
    Создаёт мок AsyncConnectionPool с правильной структурой:
    pool.connection() → async CM → conn
    conn.cursor()     → async CM → cur
    conn.commit()     → AsyncMock
    """
    cur = MagicMock()
    cur.execute = AsyncMock()

    conn = MagicMock()
    conn.cursor = MagicMock(return_value=make_async_cm(cur))
    conn.commit = AsyncMock()

    pool = MagicMock()
    pool.connection = MagicMock(return_value=make_async_cm(conn))
    pool.close = AsyncMock()

    return pool, conn, cur


# ─── save_check ─────────────────────────────────────────────────────────

async def test_save_check_without_pool_returns_false():
    """Если пул не создан — save_check тихо возвращает False."""
    db = Database(config={})
    db.pool = None

    result = await db.save_check({
        "url": "https://example.com",
        "ok": True,
        "status_code": 200,
        "response_time": 0.5,
        "reason": "OK",
        "checked_at": "2026-10-04T12:00:00+00:00",
    })

    assert result is False


async def test_save_check_success():
    """Успешная запись — возвращает True, выполняет SQL и commit."""
    pool, conn, cur = make_fake_pool()

    db = Database(config={})
    db.pool = pool

    result = await db.save_check({
        "url": "https://example.com",
        "ok": True,
        "status_code": 200,
        "response_time": 0.5,
        "reason": "OK",
        "checked_at": "2026-10-04T12:00:00+00:00",
    })

    assert result is True
    cur.execute.assert_awaited_once()
    conn.commit.assert_awaited_once()


async def test_save_check_returns_false_on_error():
    """Если SQL упал — возвращаем False, не бросаем."""
    pool, conn, cur = make_fake_pool()
    cur.execute = AsyncMock(side_effect=Exception("db error"))

    db = Database(config={})
    db.pool = pool

    result = await db.save_check({
        "url": "https://example.com",
        "ok": True,
        "status_code": 200,
        "response_time": 0.5,
        "reason": "OK",
        "checked_at": "2026-10-04T12:00:00+00:00",
    })

    assert result is False


# ─── close ──────────────────────────────────────────────────────────────

async def test_close_without_pool_is_safe():
    """Без пула — close() ничего не делает, не падает."""
    db = Database(config={})
    db.pool = None

    await db.close()  # не должно бросить исключение


async def test_close_calls_pool_close():
    """С пулом — close() вызывает pool.close() и обнуляет ссылку."""
    pool, _, _ = make_fake_pool()

    db = Database(config={})
    db.pool = pool

    await db.close()

    pool.close.assert_awaited_once()
    assert db.pool is None