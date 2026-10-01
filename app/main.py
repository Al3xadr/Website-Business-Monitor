import sys
import logging

from checker import check_site


logger = logging.getLogger(__name__)


REASON_TEXT = {
    "OK": "Site is reachable",
    "TIMEOUT": "Connection timeout",
    "CONNECTION_ERROR": "Could not connect to site",
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python app/main.py <URL>")
        sys.exit(1)

    url = sys.argv[1]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.info("Checking %s", url)

    result = check_site(url)

    if result["ok"]:
        logger.info("Site is UP: %s (%.2f s)", url, result["response_time"])
    else:
        logger.error("Site is DOWN: %s (reason: %s)", url, result["reason"])

    # ... вывод для пользователя (print) остаётся как был


if __name__ == "__main__":
    main()