import asyncio
import logging
import time
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp


logger = logging.getLogger(__name__)


async def check_site(url, timeout=5, session=None):
    """
    Асинхронно проверяет доступность сайта.
    Возвращает dict с результатом.

    session — опциональный aiohttp.ClientSession.
    Если не передан — создаётся временная сессия на один запрос.
    """
    result = {
        "url": url,
        "ok": False,
        "status_code": None,
        "response_time": None,
        "reason": None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    client_timeout = aiohttp.ClientTimeout(total=timeout)

    try:
        start = time.monotonic()

        if session is None:
            async with aiohttp.ClientSession(timeout=client_timeout) as tmp_session:
                async with tmp_session.get(url) as response:
                    result["status_code"] = response.status
        else:
            async with session.get(url, timeout=client_timeout) as response:
                result["status_code"] = response.status

        result["response_time"] = time.monotonic() - start

        if result["status_code"] is not None and 200 <= result["status_code"] <= 399:
            result["ok"] = True
            result["reason"] = "OK"
        else:
            result["reason"] = f"HTTP_{result['status_code']}"

    except asyncio.TimeoutError:
        result["reason"] = "TIMEOUT"

    except aiohttp.ClientConnectorError:
        result["reason"] = "CONNECTION_ERROR"

    except aiohttp.ClientError as e:
        logger.warning("HTTP error for %s: %s", url, e)
        result["reason"] = "CONNECTION_ERROR"

    return result

async def test_custom_timeout_passed_to_session():
    fake_session = MagicMock()
    fake_session.get.return_value = make_fake_response(200)

    await check_site("https://example.com", timeout=10, session=fake_session)

    fake_session.get.assert_called_once()
    call_args = fake_session.get.call_args
    assert call_args.args[0] == "https://example.com"

    timeout_arg = call_args.kwargs["timeout"]
    assert timeout_arg.total == 10