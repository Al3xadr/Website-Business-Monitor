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


logger = logging.getLogger("app.main")


REASON_TEXT = {
    "OK": "Site is reachable",
    "TIMEOUT": "Connection timeout",
    "CONNECTION_ERROR": "Could not connect to site",
}


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
    raw = os.getenv("WBM_TIMEOUT", "5")
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"WBM_TIMEOUT must be a number, got: {raw!r}")


def get_interval():
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


def make_check_callback(url, timeout, first_run=False):
    """
    Возвращает async callback для scheduler.

    - Первая итерация: полный отчёт
    - Смена состояния: событие 🔴 / 🟢
    - Без изменений: тихая короткая строка
    """
    state = {"first": first_run}
    tracker = StateTracker()

    async def callback():
        result = await check_site(url, timeout=timeout)
        current = "UP" if result["ok"] else "DOWN"

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
                logger.error(
                    "TRANSITION %s -> %s: %s (reason: %s)",
                    previous, current, url, result["reason"],
                )
                print()
                print(f"🔴 ALERT: {url} is DOWN (was {previous}) — {result['reason']}")
                print()
            else:
                logger.info(
                    "TRANSITION %s -> %s: %s",
                    previous, current, url,
                )
                print()
                print(f"🟢 RECOVERED: {url} is UP (was {previous})")
                print()
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

    if interval is None:
        # Режим «одна проверка»
        logger.info("Checking %s (timeout=%s)", url, timeout)
        result = await check_site(url, timeout=timeout)

        if result["ok"]:
            logger.info("Site is UP: %s (%.2f s)", url, result["response_time"])
        else:
            logger.error("Site is DOWN: %s (reason: %s)", url, result["reason"])

        print_full_report(result)
        return

    # Режим мониторинга
    logger.info("Starting monitor: %s (timeout=%s, interval=%s)",
                url, timeout, interval)

    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()

    def handle_signal(signum, frame=None):
        sig_name = signal.Signals(signum).name
        print()
        logger.info("Received %s, stopping...", sig_name)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal, sig)

    callback = make_check_callback(url, timeout, first_run=True)

    try:
        await run_forever(callback, interval, stop_event=stop_event)
    except asyncio.CancelledError:
        logger.info("Cancelled")
        stop_event.set()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # fallback: если сигнал не перехватился
        print()
        print("Interrupted")