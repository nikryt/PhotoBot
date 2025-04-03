from aiogram.enums import ParseMode
from aiogram.filters import Command


import Texts
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputFile

from app.handlers import send_typing_and_message, mes_user_history
from app.keyboards import create_inline_keyboard

help_router = Router()

@help_router.message(Command('help'))
async def  cmd_help(message: Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    keyboard = await create_inline_keyboard(
        Texts.Buttons.PHOTO_HELP,
        Texts.Buttons.BILD_HELP,
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
        Texts.Buttons.PHOTO_HELP,
        Texts.Buttons.BILD_HELP,
        callback_data={0: "Photo", 1: "Bild"}
    )
    # Удаляем исходное сообщение с кнопкой
    await callback.message.delete()
    await callback.message.answer(text=Texts.Help.MAIN, reply_markup=keyboard)
    await callback.answer()

# Обработчик нажатия на кнопку "Photo"
@help_router.callback_query(F.data == "Photo")
async def photo_help(callback: CallbackQuery, bot: Bot, state: FSMContext):
    # Создаем новую клавиатуру
    new_keyboard = await create_inline_keyboard(
        Texts.Help.CAMERA_SETUP,
        Texts.Buttons.ADD_MARKS,
        Texts.Buttons.BACK,
        callback_data={
            0: "camera_select",
            1: "add_marks",
            2: "help_back"
        },
        sizes=(2, 1)
    )

    # Редактируем и текст, и клавиатуру
    await callback.message.edit_text(
        text=Texts.Help.PHOTO_HELP_TEXT,
        reply_markup=new_keyboard
    )
    await callback.answer()


@help_router.callback_query(F.data == "camera_select")
async def camera_select_vendor(callback: CallbackQuery):
    new_keyboard = await create_inline_keyboard(
        Texts.Buttons.CAMERA_NIKON,
        Texts.Buttons.CAMERA_CANON,
        Texts.Buttons.CAMERA_SONY,
        Texts.Buttons.CAMERA_FUJIFILM,
        Texts.Buttons.BACK,
        callback_data={
            0: "nikon",
            1: "canon",
            2: "sony",
            3: "fujifilm",
            4: "help_back"
        },
        sizes=(2,2,1)
    )

    await callback.message.edit_text(text=Texts.Help.CAMERA_SELECT, parse_mode=ParseMode.HTML, reply_markup=new_keyboard)
    await callback.answer()


@help_router.callback_query(F.data == "nikon")
async def camera_setup_nikon(callback: CallbackQuery):
    new_keyboard = await create_inline_keyboard(
        Texts.Buttons.ADD_MARKS,
        Texts.Buttons.BACK,
        callback_data={
            0: "add_marks",
            1: "help_back"
        },
        sizes=(2,)
    )

    # Удаляем исходное сообщение с кнопкой
    await callback.message.delete()

    # Загружаем фото (используйте правильный путь/URL/file_id)
    photo = "AgACAgIAAxkBAAI3u2fudWaLos4eWNunSNGXEA1-NcENAALd8DEbzrpwS5f9BFc3MscyAQADAgADbQADNgQ"  # Или URL, file_id

    # Отправляем новое сообщение с фото
    await callback.message.answer_photo(
        photo=photo,
        caption=Texts.Help.CAMERA_SETUP_NIKON,  # Текст под фото
        parse_mode=ParseMode.HTML,
        reply_markup=new_keyboard  # Кнопки под фото
    )
    await callback.answer()

@help_router.callback_query(F.data == "canon")
async def camera_setup_nikon(callback: CallbackQuery):
    new_keyboard = await create_inline_keyboard(
        Texts.Buttons.ADD_MARKS,
        Texts.Buttons.BACK,
        callback_data={
            0: "add_marks",
            1: "help_back"
        },
        sizes=(2,)
    )

    await callback.message.edit_text(text=Texts.Help.CAMERA_SETUP_CANON, parse_mode=ParseMode.HTML, reply_markup=new_keyboard)
    await callback.answer()