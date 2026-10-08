import sys
import os
import signal
import logging
import asyncio
from app.monitor import Monitor
from datetime import datetime

from dotenv import load_dotenv

from app.checker import check_site
from app.scheduler import run_forever
from app.state import StateTracker
from app.notifier import TelegramNotifier
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



def make_check_callback(url, timeout, notifier, db, site_id, first_run=False):
    state = {"first": first_run}
    tracker = StateTracker()

    async def callback():
        result = await check_site(url, timeout=timeout)
        current = "UP" if result["ok"] else "DOWN"

        await db.save_check(site_id, result)   # ← site_id

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

    setup_logging()

    timeout = get_timeout()
    interval = get_interval()

    if interval is None:
        logger.error("WBM_INTERVAL is required. WBM runs as a daemon now.")
        print("Usage: set WBM_INTERVAL in .env (e.g. WBM_INTERVAL=60)")
        return

    db = Database(get_db_config())
    await db.connect()

    notifier = TelegramNotifier()
    monitor = Monitor(db, notifier, timeout)

    logger.info("Starting WBM monitor (timeout=%s, interval=%s)", timeout, interval)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def handle_signal(signum, frame=None):
        sig_name = signal.Signals(signum).name
        print()
        logger.info("Received %s, stopping...", sig_name)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal, sig)

    try:
        await run_forever(monitor.tick, interval, stop_event=stop_event)
    except asyncio.CancelledError:
        logger.info("Cancelled")
        stop_event.set()
    finally:
        await notifier.close()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("Interrupted")