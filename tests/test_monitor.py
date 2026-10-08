from unittest.mock import AsyncMock, MagicMock

from app.monitor import Monitor


def make_db_with_sites(sites):
    db = MagicMock()
    db.get_enabled_sites = AsyncMock(return_value=sites)
    db.save_check = AsyncMock(return_value=True)
    return db


def make_notifier():
    notifier = MagicMock()
    notifier.send = AsyncMock(return_value=True)
    return notifier


async def test_tick_skips_when_no_sites():
    db = make_db_with_sites([])
    notifier = make_notifier()
    monitor = Monitor(db, notifier, timeout=5)

    await monitor.tick()

    db.save_check.assert_not_awaited()
    notifier.send.assert_not_awaited()


async def test_tick_saves_check_for_each_site(monkeypatch):
    sites = [
        {"id": 1, "url": "https://a.com", "telegram_id": 111},
        {"id": 2, "url": "https://b.com", "telegram_id": 222},
    ]
    db = make_db_with_sites(sites)
    notifier = make_notifier()
    monitor = Monitor(db, notifier, timeout=5)

    async def fake_check_site(url, timeout=5):
        return {
            "url": url,
            "ok": True,
            "status_code": 200,
            "response_time": 0.1,
            "reason": "OK",
            "checked_at": "2026-10-08T12:00:00+00:00",
        }

    monkeypatch.setattr("app.monitor.check_site", fake_check_site)

    await monitor.tick()

    assert db.save_check.await_count == 2
    calls = db.save_check.await_args_list
    assert calls[0].args[0] == 1
    assert calls[1].args[0] == 2


async def test_transition_up_to_down_notifies_owner(monkeypatch):
    sites = [{"id": 1, "url": "https://a.com", "telegram_id": 999}]
    db = make_db_with_sites(sites)
    notifier = make_notifier()
    monitor = Monitor(db, notifier, timeout=5)

    responses = [
        {"ok": True, "status_code": 200, "response_time": 0.1, "reason": "OK"},
        {"ok": False, "status_code": None, "response_time": None, "reason": "TIMEOUT"},
    ]

    async def fake_check_site(url, timeout=5):
        r = responses.pop(0)
        r["url"] = url
        r["checked_at"] = "2026-10-08T12:00:00+00:00"
        return r

    monkeypatch.setattr("app.monitor.check_site", fake_check_site)

    # Tick 1: None → UP — без уведомления
    await monitor.tick()
    assert notifier.send.await_count == 0

    # Tick 2: UP → DOWN — уведомление
    await monitor.tick()
    assert notifier.send.await_count == 1
    assert notifier.send.await_args_list[0].args[0] == 999


async def test_first_check_does_not_notify(monkeypatch):
    """Первая проверка не уведомляет — состояние ранее неизвестно."""
    sites = [{"id": 1, "url": "https://a.com", "telegram_id": 111}]
    db = make_db_with_sites(sites)
    notifier = make_notifier()
    monitor = Monitor(db, notifier, timeout=5)

    async def fake_check_site(url, timeout=5):
        return {
            "url": url, "ok": True, "status_code": 200,
            "response_time": 0.1, "reason": "OK",
            "checked_at": "2026-10-08T12:00:00+00:00",
        }

    monkeypatch.setattr("app.monitor.check_site", fake_check_site)

    await monitor.tick()

    # Первая проверка — уведомление НЕ отправляется
    assert notifier.send.await_count == 0
