from unittest.mock import AsyncMock, MagicMock

from app.db import Database


# ─── Вспомогательные функции ────────────────────────────────────────────

def make_async_cm(return_value):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=return_value)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


def make_fake_pool():
    cur = MagicMock()
    cur.execute = AsyncMock()
    cur.fetchone = AsyncMock(return_value=None)
    cur.fetchall = AsyncMock(return_value=[])

    conn = MagicMock()
    conn.cursor = MagicMock(return_value=make_async_cm(cur))
    conn.commit = AsyncMock()

    pool = MagicMock()
    pool.connection = MagicMock(return_value=make_async_cm(conn))
    pool.close = AsyncMock()

    return pool, conn, cur


# ─── save_check ─────────────────────────────────────────────────────────

async def test_save_check_without_pool_returns_false():
    db = Database(config={})
    db.pool = None

    result = await db.save_check(1, {
        "ok": True,
        "status_code": 200,
        "response_time": 0.5,
        "reason": "OK",
        "checked_at": "2026-10-08T12:00:00+00:00",
    })

    assert result is False


async def test_save_check_success():
    pool, conn, cur = make_fake_pool()

    db = Database(config={})
    db.pool = pool

    result = await db.save_check(1, {
        "ok": True,
        "status_code": 200,
        "response_time": 0.5,
        "reason": "OK",
        "checked_at": "2026-10-08T12:00:00+00:00",
    })

    assert result is True
    cur.execute.assert_awaited_once()
    conn.commit.assert_awaited_once()


async def test_save_check_returns_false_on_error():
    pool, conn, cur = make_fake_pool()
    cur.execute = AsyncMock(side_effect=Exception("db error"))

    db = Database(config={})
    db.pool = pool

    result = await db.save_check(1, {
        "ok": True,
        "status_code": 200,
        "response_time": 0.5,
        "reason": "OK",
        "checked_at": "2026-10-08T12:00:00+00:00",
    })

    assert result is False


# ─── get_or_create_user ─────────────────────────────────────────────────

async def test_get_or_create_user_returns_existing():
    pool, conn, cur = make_fake_pool()
    cur.fetchone = AsyncMock(return_value=(42,))

    db = Database(config={})
    db.pool = pool

    user_id = await db.get_or_create_user(123456789)

    assert user_id == 42
    assert cur.execute.await_count == 1


async def test_get_or_create_user_creates_new():
    pool, conn, cur = make_fake_pool()
    cur.fetchone = AsyncMock(side_effect=[None, (7,)])

    db = Database(config={})
    db.pool = pool

    user_id = await db.get_or_create_user(999)

    assert user_id == 7
    assert cur.execute.await_count == 2
    conn.commit.assert_awaited_once()


async def test_get_or_create_user_without_pool():
    db = Database(config={})
    db.pool = None

    user_id = await db.get_or_create_user(123)

    assert user_id is None


# ─── add_site / list_sites / remove_site ────────────────────────────────

async def test_add_site_returns_id():
    pool, conn, cur = make_fake_pool()
    cur.fetchone = AsyncMock(return_value=(5,))

    db = Database(config={})
    db.pool = pool

    site_id = await db.add_site(1, "https://example.com")

    assert site_id == 5
    conn.commit.assert_awaited_once()


async def test_list_sites_returns_list():
    pool, conn, cur = make_fake_pool()
    cur.fetchall = AsyncMock(return_value=[
        (1, "https://a.com", None, True, "2026-10-08T00:00:00+00:00"),
        (2, "https://b.com", "My B", False, "2026-10-08T00:00:00+00:00"),
    ])

    db = Database(config={})
    db.pool = pool

    sites = await db.list_sites(1)

    assert len(sites) == 2
    assert sites[0]["url"] == "https://a.com"
    assert sites[1]["name"] == "My B"
    assert sites[1]["enabled"] is False


async def test_remove_site_returns_true_when_deleted():
    pool, conn, cur = make_fake_pool()
    cur.fetchone = AsyncMock(return_value=(1,))

    db = Database(config={})
    db.pool = pool

    result = await db.remove_site(1, user_id=42)

    assert result is True
    conn.commit.assert_awaited_once()


async def test_remove_site_returns_false_when_not_owned():
    pool, conn, cur = make_fake_pool()
    cur.fetchone = AsyncMock(return_value=None)

    db = Database(config={})
    db.pool = pool

    result = await db.remove_site(1, user_id=42)

    assert result is False


# ─── get_enabled_sites ──────────────────────────────────────────────────

async def test_get_enabled_sites_returns_sites_with_telegram_id():
    pool, conn, cur = make_fake_pool()
    cur.fetchall = AsyncMock(return_value=[
        (1, 10, "https://a.com", 111111),
        (2, 11, "https://b.com", 222222),
    ])

    db = Database(config={})
    db.pool = pool

    sites = await db.get_enabled_sites()

    assert len(sites) == 2
    assert sites[0]["url"] == "https://a.com"
    assert sites[0]["telegram_id"] == 111111
    assert sites[1]["telegram_id"] == 222222


# ─── close ──────────────────────────────────────────────────────────────

async def test_close_without_pool_is_safe():
    db = Database(config={})
    db.pool = None

    await db.close()


async def test_close_calls_pool_close():
    pool, _, _ = make_fake_pool()

    db = Database(config={})
    db.pool = pool

    await db.close()

    pool.close.assert_awaited_once()
    assert db.pool is None