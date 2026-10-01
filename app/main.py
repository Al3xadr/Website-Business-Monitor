import sys
import os
import logging
from app.checker import check_site
from dotenv import load_dotenv



logger = logging.getLogger(__name__)


REASON_TEXT = {
    "OK": "Site is reachable",
    "TIMEOUT": "Connection timeout",
    "CONNECTION_ERROR": "Could not connect to site",
}


def setup_logging():
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


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python app/main.py <URL>")
        sys.exit(1)

    url = sys.argv[1]

    setup_logging()
    logger.info("Checking %s (timeout=%s)", url, get_timeout())

    result = check_site(url, timeout=get_timeout())

    if result["ok"]:
        logger.info("Site is UP: %s (%.2f s)", url, result["response_time"])
    else:
        logger.error("Site is DOWN: %s (reason: %s)", url, result["reason"])

    print("======================")
    print("     Website Business Monitor")
    print("======================")
    print()
    print(f"URL: {url}")
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


if __name__ == "__main__":
    main()