import logging

from app.checker import check_site
from app.state import StateTracker
from app.messages import format_alert_message, format_recovered_message


logger = logging.getLogger(__name__)


class Monitor:
    """
    Мониторинг всех enabled сайтов из БД.

    Один tick = обход всех сайтов + проверка + сохранение + уведомление.

    Для каждого site_id хранится свой StateTracker (в памяти).
    При перезапуске программы состояние сбрасывается.
    """

    def __init__(self, db, notifier, timeout):
        self.db = db
        self.notifier = notifier
        self.timeout = timeout
        self.trackers = {}  # site_id → StateTracker

    async def tick(self):
        """Один цикл: проверить все enabled сайты."""
        sites = await self.db.get_enabled_sites()

        if not sites:
            logger.info("No enabled sites — nothing to check")
            return

        logger.debug("Tick: checking %d site(s)", len(sites))

        for site in sites:
            await self._check_one(site)

    async def _check_one(self, site):
        """Проверяет один сайт и обрабатывает результат."""
        url = site["url"]
        site_id = site["id"]

        result = await check_site(url, timeout=self.timeout)

        await self.db.save_check(site_id, result)

        current = "UP" if result["ok"] else "DOWN"
        tracker = self.trackers.setdefault(site_id, StateTracker())
        changed, previous = tracker.update(current)

        if not changed:
            logger.debug("%s: %s (no change)", url, current)
            return

        # Первая проверка — состояние неизвестно, не уведомляем
        if previous is None:
            logger.info("First check for %s: %s", url, current)
            return

        await self._notify(site, result, previous, current)

    async def _notify(self, site, result, previous, current):
        """Отправляет уведомление владельцу сайта."""
        if current == "DOWN":
            msg = format_alert_message(result)
            logger.warning(
                "TRANSITION %s -> %s: %s (reason: %s)",
                previous, current, site["url"], result["reason"],
            )
        else:
            msg = format_recovered_message(result)
            logger.info(
                "TRANSITION %s -> %s: %s",
                previous, current, site["url"],
            )

        await self.notifier.send(site["telegram_id"], msg)