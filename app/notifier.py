import logging
import os

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError


logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Отправляет уведомления в Telegram через aiogram.

    Токен берётся из env. chat_id передаётся в каждый send()
    (у разных пользователей — разные chat_id).
    """

    def __init__(self, token=None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.enabled = bool(self.token)
        self.bot = None

        if self.enabled:
            self.bot = Bot(token=self.token)
        else:
            logger.warning("Telegram disabled: TELEGRAM_BOT_TOKEN not set")

    async def send(self, chat_id, text):
        """
        Отправляет сообщение в указанный чат.
        Возвращает True при успехе.
        """
        if not self.enabled:
            return False

        try:
            await self.bot.send_message(chat_id=chat_id, text=text)
            logger.info("Telegram sent to %s: %s", chat_id, text[:80].replace("\n", " "))
            return True
        except TelegramAPIError as e:
            logger.error("Telegram send to %s failed: %s", chat_id, e)
            return False

    async def close(self):
        if self.bot is not None:
            await self.bot.session.close()
            logger.debug("Telegram session closed")