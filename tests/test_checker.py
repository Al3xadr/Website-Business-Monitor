import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiohttp

from app.checker import check_site


def make_fake_response(status):
    """
    Возвращает контекстный менеджер, имитирующий aiohttp-ответ.
    """
    response = MagicMock()
    response.status = status

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=response)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


async def test_http_200():
    fake_session = MagicMock()
    fake_session.get.return_value = make_fake_response(200)

    result = await check_site("https://example.com", session=fake_session)

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["reason"] == "OK"


async def test_http_404():
    fake_session = MagicMock()
    fake_session.get.return_value = make_fake_response(404)

    result = await check_site("https://example.com", session=fake_session)

    assert result["ok"] is False
    assert result["status_code"] == 404
    assert result["reason"] == "HTTP_404"


async def test_http_500():
    fake_session = MagicMock()
    fake_session.get.return_value = make_fake_response(500)

    result = await check_site("https://example.com", session=fake_session)

    assert result["ok"] is False
    assert result["status_code"] == 500
    assert result["reason"] == "HTTP_500"


async def test_timeout():
    fake_session = MagicMock()
    fake_session.get.side_effect = asyncio.TimeoutError()

    result = await check_site("https://example.com", session=fake_session)

    assert result["ok"] is False
    assert result["status_code"] is None
    assert result["response_time"] is None
    assert result["reason"] == "TIMEOUT"


async def test_connection_error():
    fake_session = MagicMock()
    fake_session.get.side_effect = aiohttp.ClientConnectorError(
        connection_key=MagicMock(), os_error=OSError("no route")
    )

    result = await check_site("https://example.com", session=fake_session)

    assert result["ok"] is False
    assert result["status_code"] is None
    assert result["response_time"] is None
    assert result["reason"] == "CONNECTION_ERROR"


async def test_result_has_common_fields():
    fake_session = MagicMock()
    fake_session.get.return_value = make_fake_response(200)

    result = await check_site("https://example.com", session=fake_session)

    assert "url" in result
    assert "ok" in result
    assert "status_code" in result
    assert "response_time" in result
    assert "reason" in result
    assert "checked_at" in result
    assert result["url"] == "https://example.com"


async def test_custom_timeout_passed_to_session():
    fake_session = MagicMock()
    fake_session.get.return_value = make_fake_response(200)

    await check_site("https://example.com", timeout=10, session=fake_session)

    fake_session.get.assert_called_once()
    call_args = fake_session.get.call_args
    assert call_args.args[0] == "https://example.com"

    timeout_arg = call_args.kwargs["timeout"]
    assert timeout_arg.total == 10