from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.exceptions import TelegramAPIError

from app.notifier import TelegramNotifier


async def test_disabled_without_token():
    notifier = TelegramNotifier(token=None)
    assert notifier.enabled is False
    assert notifier.bot is None
    assert await notifier.send(123, "test") is False


async def test_send_success():
    with patch("app.notifier.Bot") as MockBot:
        mock_bot_instance = MagicMock()
        mock_bot_instance.send_message = AsyncMock()
        MockBot.return_value = mock_bot_instance

        notifier = TelegramNotifier(token="test_token")
        assert notifier.enabled is True

        result = await notifier.send(12345, "hello")

        assert result is True
        mock_bot_instance.send_message.assert_awaited_once_with(
            chat_id=12345, text="hello"
        )


async def test_send_failure_returns_false():
    with patch("app.notifier.Bot") as MockBot:
        mock_bot_instance = MagicMock()
        mock_bot_instance.send_message = AsyncMock(
            side_effect=TelegramAPIError(method="sendMessage", message="boom")
        )
        MockBot.return_value = mock_bot_instance

        notifier = TelegramNotifier(token="test_token")
        result = await notifier.send(123, "hello")

        assert result is False


async def test_send_to_different_chats():
    """Один и тот же notifier шлёт в разные чаты."""
    with patch("app.notifier.Bot") as MockBot:
        mock_bot_instance = MagicMock()
        mock_bot_instance.send_message = AsyncMock()
        MockBot.return_value = mock_bot_instance

        notifier = TelegramNotifier(token="test_token")
        await notifier.send(111, "to first")
        await notifier.send(222, "to second")

        assert mock_bot_instance.send_message.await_count == 2
        calls = mock_bot_instance.send_message.await_args_list
        assert calls[0].kwargs["chat_id"] == 111
        assert calls[1].kwargs["chat_id"] == 222


async def test_close_closes_session():
    with patch("app.notifier.Bot") as MockBot:
        mock_bot_instance = MagicMock()
        mock_bot_instance.session = MagicMock()
        mock_bot_instance.session.close = AsyncMock()
        MockBot.return_value = mock_bot_instance

        notifier = TelegramNotifier(token="test_token")
        await notifier.close()

        mock_bot_instance.session.close.assert_awaited_once()


async def test_close_is_safe_when_disabled():
    notifier = TelegramNotifier(token=None)
    await notifier.close()