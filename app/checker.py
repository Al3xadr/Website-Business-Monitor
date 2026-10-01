import time
from datetime import datetime, timezone
import requests
import logging



logger = logging.getLogger(__name__)

def check_site(url):
    result = {
        "url": url,
        "ok": False,
        "status_code": None,
        "response_time": None,
        "reason": None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        end = time.time()

        result["status_code"] = response.status_code
        result["response_time"] = end - start

        if 200 <= response.status_code <= 399:
            result["ok"] = True
            result["reason"] = "OK"
        else:
            result["reason"] = f"HTTP_{response.status_code}"

    except requests.exceptions.Timeout:
        result["reason"] = "TIMEOUT"

    except requests.exceptions.ConnectionError:
        result["reason"] = "CONNECTION_ERROR"

    return result