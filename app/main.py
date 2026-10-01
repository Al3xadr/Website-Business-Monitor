import sys
import logging
import os

from checker import check_site


logger = logging.getLogger(__name__)


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

    # Handler для консоли
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    # Handler для файла
    file_handler = logging.FileHandler("logs/wbm.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def main():
    if len(sys.argv) < 2:
        print("Usage: python app/main.py <URL>")
        sys.exit(1)

    url = sys.argv[1]

    setup_logging()
    logger.info("Checking %s", url)

    result = check_site(url)

    if result["ok"]:
        logger.info("Site is UP: %s (%.2f s)", url, result["response_time"])
    else:
        logger.error("Site is DOWN: %s (reason: %s)", url, result["reason"])

    # ... остальной print-вывод для пользователя


if __name__ == "__main__":
    main()