from telegram import Bot
from config import CHAT_IDs, TELEGRAM_TOKEN1


class TelegramBotService:
    """
    Класс, отвечающий за взаимодействие с телеграмм ботом вне рамок ответа на запросы
    """

    def __init__(self):
        self.bot = Bot(token=TELEGRAM_TOKEN1)

    async def send_message(self, text):
        for chat_id in CHAT_IDs:
            await self.bot.send_message(chat_id=chat_id, text=text)
