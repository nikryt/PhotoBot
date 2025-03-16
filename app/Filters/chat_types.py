import os
import logging
from  aiogram.filters import Filter
from aiogram import types, Bot
from dotenv import load_dotenv


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]):
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def   __call__(self, message: types.Message, bot: Bot) -> bool:
        load_dotenv()
        admin = int(os.getenv('ADMIN')) # Преобразуем строку в число
        # logging.info(str(admin))
        return message.from_user.id == admin