import logging
import os

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError


logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Отправляет уведомления в Telegram через aiogram.
    Если токен или chat_id не заданы — работает в режиме "выключен".
    """

    def __init__(self, token=None, chat_id=None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)
        self.bot = None

        if self.enabled:
            self.bot = Bot(token=self.token)
        else:
            logger.warning(
                "Telegram disabled: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set"
            )

    async def send(self, text):
        """Отправляет сообщение. Возвращает True при успехе."""
        if not self.enabled:
            return False

        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text)
            logger.info("Telegram sent: %s", text[:80].replace("\n", " "))
            return True
        except TelegramAPIError as e:
            logger.error("Telegram send failed: %s", e)
            return False

    async def close(self):
        """Закрывает сессию бота."""
        if self.bot is not None:
            await self.bot.session.close()
            logger.debug("Telegram session closed")