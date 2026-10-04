import sys
import os
import signal
import logging
import asyncio

from datetime import datetime

from dotenv import load_dotenv

from app.checker import check_site
from app.scheduler import run_forever
from app.state import StateTracker
from app.notifier import TelegramNotifier
from app.config import setup_logging, get_timeout, get_interval
from app.config import setup_logging, get_timeout, get_interval, get_db_config
from app.db import Database



logger = logging.getLogger("app.main")


REASON_TEXT = {
    "OK": "Site is reachable",
    "TIMEOUT": "Connection timeout",
    "CONNECTION_ERROR": "Could not connect to site",
}


def print_full_report(result):
    print("======================")
    print("     Website Business Monitor")
    print("======================")
    print()
    print(f"URL: {result['url']}")
    print()

    if result["status_code"] is not None:
        print(f"HTTP status: {result['status_code']}")

    if result["response_time"] is not None:
        print(f"Response time: {result['response_time']:.2f} seconds")

    if result["reason"] in REASON_TEXT:
        print(f"Reason: {REASON_TEXT[result['reason']]}")
    elif result["reason"]:
        print(f"Reason: {result['reason']}")

    print()
    print(f"Status: {'UP' if result['ok'] else 'DOWN'}")
    print()


def print_short_line(result):
    ts = datetime.now().strftime("%H:%M:%S")
    status = "UP  " if result["ok"] else "DOWN"

    if result["ok"]:
        print(f"[{ts}] {status} {result['url']} ({result['response_time']:.2f}s)")
    else:
        print(f"[{ts}] {status} {result['url']} ({result['reason']})")



def format_alert_message(result):
    """Форматирует сообщение о падении для Telegram."""
    dt = datetime.fromisoformat(result["checked_at"])
    time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "🔴 Website DOWN",
        "",
        f"URL: {result['url']}",
    ]

    if result["status_code"] is not None:
        lines.append(f"HTTP status: {result['status_code']}")

    lines.append(f"Reason: {result['reason']}")
    lines.append(f"Time: {time_str}")

    return "\n".join(lines)


def format_recovered_message(result):
    """Форматирует сообщение о восстановлении для Telegram."""
    from datetime import datetime

    dt = datetime.fromisoformat(result["checked_at"])
    time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "🟢 Website RECOVERED",
        "",
        f"URL: {result['url']}",
    ]

    if result["status_code"] is not None:
        lines.append(f"HTTP status: {result['status_code']}")

    if result["response_time"] is not None:
        lines.append(f"Response time: {result['response_time']:.2f} seconds")

    lines.append(f"Time: {time_str}")

    return "\n".join(lines)



def make_check_callback(url, timeout, notifier, db, first_run=False):
    state = {"first": first_run}
    tracker = StateTracker()

    async def callback():
        result = await check_site(url, timeout=timeout)
        current = "UP" if result["ok"] else "DOWN"

        await db.save_check(result)

        changed, previous = tracker.update(current)

        if state["first"]:
            if result["ok"]:
                logger.info("Site is UP: %s (%.2f s)", url, result["response_time"])
            else:
                logger.error("Site is DOWN: %s (reason: %s)", url, result["reason"])
            print_full_report(result)
            state["first"] = False
            return

        if changed:
            if current == "DOWN":
                msg = format_alert_message(result)
                logger.error(
                    "TRANSITION %s -> %s: %s (reason: %s)",
                    previous, current, url, result["reason"],
                )
            else:
                msg = format_recovered_message(result)
                logger.info("TRANSITION %s -> %s: %s", previous, current, url)

            print()
            print(msg)
            print()
            await notifier.send(msg)
        else:
            logger.debug("Site is UP: %s (%.2f s)", url, result["response_time"])
            print_short_line(result)

    return callback

async def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python -m app.main <URL>")
        sys.exit(1)

    url = sys.argv[1]

    setup_logging()

    timeout = get_timeout()
    interval = get_interval()

    # Подключаемся к БД (даже в режиме одной проверки — полезно)
    db = Database(get_db_config())
    await db.connect()

    try:
        if interval is None:
            # Режим «одна проверка»
            logger.info("Checking %s (timeout=%s)", url, timeout)
            result = await check_site(url, timeout=timeout)

            await db.save_check(result)

            if result["ok"]:
                logger.info("Site is UP: %s (%.2f s)", url, result["response_time"])
            else:
                logger.error("Site is DOWN: %s (reason: %s)", url, result["reason"])

            print_full_report(result)
            return

        # Режим мониторинга
        logger.info(
            "Starting monitor: %s (timeout=%s, interval=%s)",
            url, timeout, interval,
        )

        notifier = TelegramNotifier()

        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def handle_signal(signum, frame=None):
            sig_name = signal.Signals(signum).name
            print()
            logger.info("Received %s, stopping...", sig_name)
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_signal, sig)

        callback = make_check_callback(url, timeout, notifier, db, first_run=True)

        try:
            await run_forever(callback, interval, stop_event=stop_event)
        except asyncio.CancelledError:
            logger.info("Cancelled")
            stop_event.set()
        finally:
            await notifier.close()
    finally:
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("Interrupted")