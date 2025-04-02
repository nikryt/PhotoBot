from aiogram.enums import ParseMode
from aiogram.filters import Command


import Texts
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.handlers import send_typing_and_message, mes_user_history
from app.keyboards import create_inline_keyboard

help_router = Router()

@help_router.message(Command('help'))
async def  cmd_help(message: Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    keyboard = await create_inline_keyboard(
        Texts.Help.PHOTO_HELP,
        Texts.Help.BILD_HELP,
        callback_data={
            0: "Photo",
            1: "Bild"
        }
    )
    await send_typing_and_message(
        message.chat.id, bot, # Передаём chat.id и bot как позиционный аргумент
        text=Texts.Help.MAIN, # Передаём text как именованный аргумент
        reply_markup=keyboard,
        state=state # Передаём state как именованный аргумент, указали state явно
    )

# Новый обработчик для кнопки Назад
@help_router.callback_query(F.data == "help_back")
async def back_to_main_help(callback: CallbackQuery, bot: Bot, state: FSMContext):
    # Создаем оригинальную клавиатуру из команды /help
    keyboard = await create_inline_keyboard(
        Texts.Help.PHOTO_HELP,
        Texts.Help.BILD_HELP,
        callback_data={0: "Photo", 1: "Bild"}
    )

    await callback.message.edit_text(text=Texts.Help.MAIN, reply_markup=keyboard)
    await callback.answer()

# Обработчик нажатия на кнопку "Photo"
@help_router.callback_query(F.data == "Photo")
async def photo_help(callback: CallbackQuery, bot: Bot, state: FSMContext):
    # Создаем новую клавиатуру
    new_keyboard = await create_inline_keyboard(
        Texts.Help.CAMERA_SETUP,
        Texts.Help.ADD_MARKS,
        Texts.Help.BACK,
        callback_data={
            0: "camera_setup",
            1: "add_marks",
            2: "help_back"  # Новый callback для кнопки Назад
        },
        sizes=(2, 1)
    )

    # Редактируем и текст, и клавиатуру
    await callback.message.edit_text(
        text=Texts.Help.PHOTO_HELP_TEXT,  # Новый текст для раздела
        reply_markup=new_keyboard
    )
    await callback.answer()



@help_router.callback_query(F.data == "camera_setup")
async def camera_setup_help(callback: CallbackQuery):
    new_keyboard = await create_inline_keyboard(
        Texts.Help.ADD_MARKS,
        Texts.Help.BACK,
        callback_data={
            0: "add_marks",
            1: "help_back"  # Новый callback для кнопки Назад
        },
        sizes=(2,)
    )

    await callback.message.edit_text(text=Texts.Help.CAMERA_SETUP_TEXT, parse_mode=ParseMode.HTML, reply_markup=new_keyboard)
    await callback.answer()