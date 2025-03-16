

from aiogram import F, Router, types, Bot
from aiogram.filters import Command

from app.Filters.chat_types import ChatTypeFilter, IsAdmin  # импортировали наши личные фильтры
import app.keyboards as kb

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

@admin_router.message(Command("admin"))
async def admin_keyboard(message: types.Message):
    await message.answer("тестируем админку", reply_markup=kb.admin)
