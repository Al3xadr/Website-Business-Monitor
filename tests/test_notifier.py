from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.exceptions import TelegramAPIError

from app.notifier import TelegramNotifier


async def test_disabled_without_token():
    notifier = TelegramNotifier(token=None, chat_id=None)
    assert notifier.enabled is False
    assert notifier.bot is None
    assert await notifier.send("test") is False


async def test_disabled_without_chat_id():
    notifier = TelegramNotifier(token="test_token", chat_id=None)
    assert notifier.enabled is False
    assert await notifier.send("test") is False


async def test_send_success():
    with patch("app.notifier.Bot") as MockBot:
        mock_bot_instance = MagicMock()
        mock_bot_instance.send_message = AsyncMock()
        MockBot.return_value = mock_bot_instance

        notifier = TelegramNotifier(token="test_token", chat_id="123")
        assert notifier.enabled is True

        result = await notifier.send("hello")

        assert result is True
        mock_bot_instance.send_message.assert_awaited_once_with(
            chat_id="123", text="hello"
        )


async def test_send_failure_returns_false():
    with patch("app.notifier.Bot") as MockBot:
        mock_bot_instance = MagicMock()
        mock_bot_instance.send_message = AsyncMock(
            side_effect=TelegramAPIError(method="sendMessage", message="boom")
        )
        MockBot.return_value = mock_bot_instance

        notifier = TelegramNotifier(token="test_token", chat_id="123")
        result = await notifier.send("hello")

        assert result is False


async def test_close_closes_session():
    with patch("app.notifier.Bot") as MockBot:
        mock_bot_instance = MagicMock()
        mock_bot_instance.session = MagicMock()
        mock_bot_instance.session.close = AsyncMock()
        MockBot.return_value = mock_bot_instance

        notifier = TelegramNotifier(token="test_token", chat_id="123")
        await notifier.close()

        mock_bot_instance.session.close.assert_awaited_once()


async def test_close_is_safe_when_disabled():
    notifier = TelegramNotifier(token=None, chat_id=None)
    # Не должно бросить исключение
    await notifier.close()