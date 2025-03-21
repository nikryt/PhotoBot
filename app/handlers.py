import logging
from dotenv import load_dotenv
import Texts
import os
import re
import asyncio

from datetime import datetime
from pathlib import Path
from aiogram import F, Router, types, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ContentType, ChatAction
from aiogram.enums import ParseMode
#Импортировали тексты из отдельного файла
from Texts import Messages, Buttons, StatesText, Help
from app.database.models import Item
from app.generate import ai_generate
from app.Filters.chat_types import ChatTypeFilter # импортировали наши личные фильтры

import app.keyboards as kb
import app.database.requests as rq
import app.Sheets.function as fu
import app.SerialNumber as sn
import app.Utils.validators as vl

from aiogram.utils.formatting import PhoneNumber
from app.database.requests import get_item
from requests import session

#from aiohttp.web_fileresponse import content_type
#from google.auth import message

#Объект класса router Router
router = Router()
# включаем фильтр на работу только в приватных чатах из созданного нами фильтра
router.message.filter(ChatTypeFilter(['private']))

class StartState(StatesGroup):
    active = State()  # Состояние, в котором будем удалять сообщения


class Register(StatesGroup):
    # last_bot_message_id = State()
    tg_id = State()
    nameRU = State()
    nameEN = State()
    idn = State()
    mailcontact = State()
    tel = State()
    role = State()
    photofile1 = State()
    photofile2 = State()
    photofile3 = State()
    serial1 = State()
    serial2 = State()
    serial3 = State()
    verify = State()
    nameRU2 = State()
    nameEN2 = State()
    idn2 = State()
    mailcontact2 = State()
    tel2 = State()
    role2 = State()
    texts = StatesText.REGISTER

class Gen(StatesGroup):
    wait = State()
    result = State()

class Find(StatesGroup):
    wait = State()    # Ожидание ввода кода
    send = State()    # Отправка результатов
    exclude = State() # Фильтрация результатов

class AdminApproval(StatesGroup):
    waiting = State()



# Переменная для хранения message_id последнего сообщения бота
# last_bot_message_id = None

# Глобальная переменная для условия перехода в редактирования
edit = None

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await asyncio.sleep(1)
    await state.set_state(StartState.active)

    # Проверка наличия пользователя в таблице items
    user_item = await rq.get_item_by_tg_id(message.from_user.id)
    await rq.set_user(message.from_user.id)  # Всегда обновляем users

    if user_item:
        # Получаем данные пользователя
        role_name = await rq.get_role_name(user_item.role)
        logging.info(f'роль у пользователя: {role_name}')
        keyboard = await kb.get_role_keyboard(role_name)
        if role_name == "Фотограф":
            await message.answer_photo(
                photo='AgACAgIAAxkBAAIuR2fashuwXR4JxPqppsyLq2s6YItVAALZ8jEbEyXZSoH5VvsTs1cBAQADAgADeQADNgQ',
                caption=f"👋 Фотограф: {user_item.nameRU}!"
            )
            await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            await asyncio.sleep(1)
            await message.answer(text=Messages.INTRO_PHOTO, parse_mode=ParseMode.HTML,
                reply_markup=keyboard)
        elif role_name == "Билд-редактор":
            await message.answer_photo(
                photo='AgACAgIAAxkBAAIuTGfatOPysGg2vhxRh9MQnXq7aCXOAALt8jEbEyXZSuZMham3gcOVAQADAgADeQADNgQ',
                caption=f"👋 Билд-Редкатор: {user_item.nameRU}!"
            )
            await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            await asyncio.sleep(1)
            await message.answer(text=Messages.INTRO_BILD, parse_mode=ParseMode.HTML,
                reply_markup=keyboard)
        elif role_name == "Менеджер":
            await message.answer_photo(
                photo='AgACAgIAAxkBAAIuTmfatYlB48bNskC7axaoEpWmfpc3AALx8jEbEyXZSrPOh6NQcu0XAQADAgADeQADNgQ',
                caption=f"👋 Манеджер: {user_item.nameRU}!"
            )
            await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            await asyncio.sleep(1)
            await message.answer(text=Messages.INTRO_MANAGER, parse_mode=ParseMode.HTML,
                reply_markup=keyboard)
        else:
            await message.answer_photo(
                photo='AgACAgIAAxkBAAPgZ361se9D_xn8AwRI7Y1gBmdmTiwAAgfrMRsQmvlLUMXQ9_Z9HXABAAMCAAN5AAM2BA',
                caption=f"👋 Кто ты? {user_item.nameRU}!"
            )
            await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            await asyncio.sleep(1)
            await message.answer(text=Messages.INTRO_OTHER, parse_mode=ParseMode.HTML,
                reply_markup=keyboard)
        await state.clear()

    else:
        await message.answer_photo(
            photo='AgACAgIAAxkBAAPgZ361se9D_xn8AwRI7Y1gBmdmTiwAAgfrMRsQmvlLUMXQ9_Z9HXABAAMCAAN5AAM2BA',
            caption=Messages.START.format(name=message.from_user.full_name),
        )
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        await asyncio.sleep(1)
        await message.answer(text=Messages.INTRO, parse_mode=ParseMode.HTML
        )

# # Старое приветсвие без проверки на регистрацию
# @router.message(CommandStart())
# # асинхронная функция cmd_start которая принимает в себя объект Massage
# async def cmd_start(message: Message, state: FSMContext, bot: Bot,):
# # внутри функции cmd_start обращаемся к методу answer, он позволяет отвечать этому же пользователю
# #     await message.answer('Привет!', reply_markup=kb.main)
# # отправляем на команду старт фотографию с подписью и клавиатуру main
#     await  state.clear()
#     # await mes_user_history(message, state)
#     await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
#     await asyncio.sleep(1)
#     await state.set_state(StartState.active)
#     await message.answer_photo(photo='AgACAgIAAxkBAAPgZ361se9D_xn8AwRI7Y1gBmdmTiwAAgfrMRsQmvlLUMXQ9_Z9HXABAAMCAAN5AAM2BA',
#                                caption=Messages.START.format(name=message.from_user.full_name)
#                                # reply_markup=kb.main)
#     )
#     await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
#     await asyncio.sleep(1)
#     await message.answer(text=Messages.INTRO, parse_mode=ParseMode.HTML)
#     # Записываем в БД пользователя с его id
#     await rq.set_user(message.from_user.id)
# # Конец старого приветсвия без проверки на регистрацию


# отправляем методом ответа на сообщение стикер по его ID
#     await message.reply_sticker(sticker='CAACAgIAAxkBAAPYZ36b1AUNHQg55cEEfzilVTX1lCYAArkRAAJClVFLVmGP6JmH07A2BA', reply_markup=ReplyKeyboardRemove())
# Получаем ID пользователя и Имя из самого первого сообщения
#    await message.reply(f'Привет :) \nТвой ID: {message.from_user.id}\nИмя: {message.from_user.first_name}\n'
#                        f'Фамилия: {message.from_user.last_name}\nНик: @{message.from_user.username}')
#   await message.reply('Как дела?')

@router.message(Command('help'))
async def  cmd_help(message: Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    await send_typing_and_message(
        message.chat.id, bot, # Передаём chat.id и bot как позиционный аргумент
        text=Help.MAIN, # Передаём text как именованный аргумент
        state=state # Передаём state как именованный аргумент, указали state явно
    )


# Общая логика для обработки регистрации вызов ко команде или нажатию инлайн кнопки (callback)
async def register_handler(message: Message, state: FSMContext, bot: Bot, tg_id: int = None):
    await state.clear()
    # Если tg_id не передан, берем из сообщения
    if not tg_id:
        tg_id = message.from_user.id
    logging.info(f'Текущий id: {tg_id}')

    # # Принудительная проверка дубликатов
    # await rq.delete_duplicates(tg_id)

    current_user = await rq.get_item_by_tg_id(tg_id)
    logging.info(f'Текущий пользователь после очистки: {current_user}')

    if current_user:
        await state.update_data(is_edit=True, item_id=current_user.id)  # Сохраняем ID для обновления)
        text = (
            "✏️ Режим редактирования. Введите новые данные.\n"
            "Сперва ФИО на русском языке:"
        )
    else:
        text = "✅ Начнём регистрацию.\nВведите ваше ФИО на русском языке"

    await send_typing_and_message(
        message.chat.id,
        bot,
        text,
        state,
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Register.nameRU)

# Обработчик команды /register
@router.message(StateFilter('*'), Command('register'))
async def register_via_command(message: Message, state: FSMContext, bot: Bot):
    # Проверяем статус регистрации
    if not await rq.get_registration_status():
        await message.answer("⚠️ Регистрация временно приостановлена администратором.")
        return
    else:
        await register_handler(message, state, bot)


# Обработчик inline-кнопки "редактировать данные"
@router.callback_query(F.data == 'edit_data')
async def register_via_schedule(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # # Проверяем статус регистрации даже для редактирования
    # if not await rq.get_registration_status():
    #     await callback.answer("⚠️ Редактирование временно недоступно", show_alert=True)
    #     return
    await callback.answer()  # Обязательно отвечаем на callback
    # Получаем ID пользователя из callback, а не из сообщения
    tg_id = callback.from_user.id
    logging.info(f"Обработка кнопки редактирования. User ID: {tg_id}")
    await register_handler(callback.message, state, bot, tg_id)



# # Функция регистрации вызов только по обычной команде
# @router.message(StateFilter('*'), Command('register'))
# async def register(message: Message, state: FSMContext, bot: Bot):
#     await state.clear()
#     current_user = await rq.get_item_by_tg_id(message.from_user.id)
#     # запишем команды для ее удаления
#     await mes_user_history(message, state)
#     if current_user:  # Если пользователь уже зарегистрирован
#         await state.update_data(is_edit=True)
#         await send_typing_and_message(
#             message.chat.id, bot,
#             "✏️ Режим редактирования. Введите новые данные.\n"
#             "Сперва ФИО на русском языке:",
#             state, reply_markup=ReplyKeyboardRemove()
#         )
#     else:
#         await send_typing_and_message(
#             message.chat.id, bot,
#             "✅ Начнём регистрацию.",
#             state, reply_markup=ReplyKeyboardRemove()
#         )
#         await send_typing_and_message(
#             message.chat.id, bot,
#             f'Введите ваше ФИО на русском языке',
#             state
#         )
#     # Активируем состояние диалога
#     await state.set_state(Register.nameRU)


async def menu_core_handler(source: Message | CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()

    # Получаем объект сообщения в зависимости от типа источника
    message = source if isinstance(source, Message) else source.message

    # Проверяем наличие пользователя в системе
    user_item = await rq.get_item_by_tg_id(message.from_user.id)

    if user_item:
        # Пользователь зарегистрирован - показываем персональное меню
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        await asyncio.sleep(1)

        role_name = await rq.get_role_name(user_item.role)
        keyboard = await kb.get_role_keyboard(role_name)

        # Формируем ответ аналогично /start
        caption = f"👋 {role_name}: {user_item.nameRU}!"
        text = {
            "Фотограф": Messages.INTRO_PHOTO,
            "Билд-редактор": Messages.INTRO_BILD,
            "Менеджер": Messages.INTRO_MANAGER
        }.get(role_name, Messages.INTRO_OTHER) # Сообщение для не определённых ролей.

        # await message.answer_photo(
        #     photo='AgACAgIAAxkBAAPgZ361se9D_xn8AwRI7Y1gBmdmTiwAAgfrMRsQmvlLUMXQ9_Z9HXABAAMCAAN5AAM2BA',
        #     caption=caption
        # )
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        await asyncio.sleep(1)
        await message.answer(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    else:
        # Пользователь не зарегистрирован - сообщаем об ошибке
        error_text = "🚫 Персональное меню недоступно. Для доступа необходимо пройти регистрацию! /register"

        if isinstance(source, CallbackQuery):
            await source.answer(error_text, show_alert=True)
        else:
            await message.answer(error_text)


# Обработчик команды /menu
@router.message(Command('menu'))
async def menu_command(message: Message, state: FSMContext, bot: Bot):
    await menu_core_handler(message, state, bot)


# Обработчик callback menu_personal
@router.callback_query(F.data == 'menu_personal')
async def menu_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await menu_core_handler(callback, state, bot)
    await callback.answer()  # Убираем "часики" на кнопке



#-----------------------------------------------------------------------------------------------------------------------
#Проверяем новые функции
#-----------------------------------------------------------------------------------------------------------------------

# Главный обработчик для состояния StartState
@router.message(StateFilter(StartState.active), ~F.command)
async def handle_start_state(message: types.Message, bot: Bot):
    if not message.text or not message.text.startswith('/'):
    # """Удаляем все сообщения кроме команд"""
        try:
            # Удаляем сообщение пользователя
            await message.delete()

            # Отправляем уведомление и удаляем его через 3 секунды
            notify = await message.answer("⚠️ Разрешены только команды!")
            await asyncio.sleep(3)
            await notify.delete()

        except Exception as e:
            print(f"Ошибка при обработке сообщения: {e}")

# # Удаляем любые сообщения вне активного диалога.
# @router.message()
# async def handle_other_messages(message: types.Message, bot: Bot):
#     # Если сообщение не команда и состояние не установлено
#     if not message.text.startswith('/'):
#         await asyncio.sleep(1)
#         await delete_message_safe(message.chat.id, message.message_id, bot)
#         msg = await message.answer("ℹ️ Для начала работы используйте /команды")
#         await asyncio.sleep(2)
#         await msg.delete()
# # Обработчик для сообщений В АКТИВНОМ диалоге
# @router.message(StateFilter(None))
# async def handle_dialog(message: Message, state: FSMContext, bot: Bot):
#     # Здесь обработка сообщений в состоянии registered
#     await message.delete()
#     # ... ваша логика обработки ...
#     await message.answer("✅ Сообщение получено")

# Функция записи сообщений пользователя в историю
async  def mes_user_history(message: Message, state: FSMContext):
    data = await state.get_data()
    message_history = data.get('message_history', [])
    message_history.append(message.message_id)
    await state.update_data(message_history=message_history)
    print(f'Записали от юзера: {message_history}')

# Функция для безопасного удаления списка сообщений
async def delete_message_safe(chat_id: int, message_id: int, bot: Bot):
    """Безопасное удаление одного сообщения"""
    try:
        await asyncio.sleep(0.3)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

async def delete_all_previous_messages(chat_id: int, state: FSMContext, bot: Bot):
    """Удаление всех сообщений из истории и очистка хранилища"""
    data = await state.get_data()
    messages_to_delete = data.get("message_history", [])
    print(f'Del: {messages_to_delete}')
    # Удаляем все сообщения из истории
    for msg_id in messages_to_delete:
        await delete_message_safe(chat_id, msg_id, bot)
    # Очищаем историю
    await state.update_data(message_history=[])

# Функция анимации печати и обновления State с внесением сообщения в историю.
async def send_typing_and_message(chat_id: int, bot: Bot, text: str, state: FSMContext = None, reply_markup=None):
    """
    Отправляет сообщение с анимацией печати и добавляет его в историю сообщений.

    Args:
        chat_id (int): ID чата.
        bot (Bot): Объект бота.
        text (str): Текст сообщения.
        state (FSMContext): Состояние FSM.
        reply_markup: Клавиатура для сообщения.

    Returns:
        Message: Отправленное сообщение.
    """
    await bot.send_chat_action(chat_id, ChatAction.TYPING)
    await asyncio.sleep(1)  # Имитация задержки печати
    message = await bot.send_message(chat_id, text, reply_markup=reply_markup)
    # if state:
    #     await state.update_data(message_history=[message.message_id])
    # Обновление истории сообщений
    if state:
        data = await state.get_data()
        message_history = data.get('message_history', [])
        message_history.append(message.message_id)
        await state.update_data(message_history=message_history)
        print(f'Записали от бота: {message_history}')
    return message




#Функция получения инициалов
async def get_initials(nameEN: str) -> str:
    return ''.join([part[0].upper() for part in nameEN.split() if part])

#Функция перевода в латиницу
async def transliterate_russian_to_eng(name_ru: str) -> str:
    """
    Транслитерирует русские ФИО в английские согласно правилам загранпаспортов РФ.
    Пример: 'Иванов Иван Иванович' → 'Ivanov Ivan Ivanovich'
    """
    translit_dict = Texts.Translit_en.EN
    translated = []
    for part in name_ru.split():
        translit_part = []
        for char in part:
            translit_part.append(translit_dict.get(char, char))

        # Собираем часть имени и форматируем регистр
        formatted_part = ''.join(translit_part)
        if formatted_part:
            formatted_part = formatted_part[0].upper() + formatted_part[1:].lower()
        translated.append(formatted_part)

    return ' '.join(translated)

#Функция проверки регистра текста ФИО
async def registr_fio(name_ru: str) -> str:
    # Инициализация списка
    translated = []
    # Обработка каждой части имени
    for part in name_ru.split():
        # Форматирование (первая буква заглавная, остальные строчные)
        formatted_part = part.strip().capitalize()
        if formatted_part:  # Пропускаем пустые строки
            translated.append(formatted_part)

    return " ".join(translated) if translated else "Ошибка: пустое имя"


# Обработчик для медиа групп (документов или фото)

# Временное хранилище для медиа групп (лучше использовать Redis или БД в продакшене)
media_groups_cache = {}

async def process_documents(documents: list, username: int, bot: Bot) -> list:
    user_dir = f"downloads/{username}"
    os.makedirs(user_dir, exist_ok=True)
    saved_files = []
    for doc in documents:
        file_id = doc["file_id"]
        file_name = doc["file_name"] or f"file_{file_id[:6]}"
        file = await bot.get_file(file_id)
        file_path = f"{user_dir}/{file_name}"
        await bot.download_file(file.file_path, file_path)
        saved_files.append(file_path)

    return saved_files

# функция сравнения данных при запросе к админу о изменениях.
async def generate_diff_message(old_item: Item, new_data: dict) -> str:
    diff = []
    fields = {
        'nameRU': 'Имя (RU)',
        'nameEU': 'Имя (EN)',
        'idn': 'Инициалы',
        'tel': 'Телефон',
        'mailcontact': 'Контакты',
        'serial1': 'Серийник 1',
        'serial2': 'Серийник 2',
        'serial3': 'Серийник 3',
        'role': 'Роль'
    }

    for field, name in fields.items():
        old_val = getattr(old_item, field, 'не указано')
        new_val = new_data.get(field, 'не указано')

        if str(old_val) != str(new_val):
            diff.append(
                f"▫️ {name}:\n"
                f"Было: {old_val}\n"
                f"Стало: {new_val}\n"
            )

    return "\n".join(diff) if diff else "Нет изменений в основных полях"

#-----------------------------------------------------------------------------------------------------------------------
#Проверяем новые функции
#-----------------------------------------------------------------------------------------------------------------------


@router.message(F.photo, StateFilter(Register.photofile1, Register.photofile2, Register.photofile3))
async def forward_message(message: Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    # Пересылаем фото
    await bot.forward_message('-1002378314584', message.from_user.id, message.message_id)
    # Отправляем ID фото в тот же чат
    await bot.send_message('-1002378314584', f'ID фото: {message.photo[-1].file_id}')
    # Отправляем ответ пользователю
    await send_typing_and_message(message.chat.id, bot, Texts.Messages.PHOTO, state)
    await send_typing_and_message(message.chat.id, bot,f'ID фото: {message.photo[-1].file_id}', state)


# @router.message(F.document)
# async def forward_message(message: Message, bot: Bot):
#     await bot.forward_message('-1002378314584', message.from_user.id, message.message_id)
#     await message.answer('Спасибо что отправили фотографию документом.')



#Функция для сохранения полученных документов в папке Download. Вызывается 3 раза в момент получения фотографий.
async def save_document(message: types.Message, bot: Bot):
    document = message.document
    file_id = document.file_id  # Получаем id документа
    file_name = document.file_name  # Получаем имя документа
    sender_name = message.from_user.username  # Получаем имя отправителя сообщения
    # Получаем информацию о файле
    file = await bot.get_file(file_id)
    file_path = file.file_path
    # Создаем папку для сохранения файлов с ником отправителя, если её еще нет
    os.makedirs(f'downloads/{sender_name}', exist_ok=True)
    # Скачиваем файл
    await bot.download_file(file_path, f'downloads/{sender_name}/{file_name}')
    # await sn.main(message)
    # await message.answer('Документ успешно сохранен')

# Отдельный Роутер для вызова функции сохранения документа
# @router.message(F.document)
# async def process_document(message: types.Message, bot: Bot):
#     await save_document(message, bot)

# @router.message(F.text == 'ФИО')
# async def fio(message: Message):
#     await message.answer('Выберите что изменить', reply_markup=kb.fio)

@router.callback_query(F.data == 'ru')
async  def fio(callback: CallbackQuery):
    await callback.answer('Вы выбрали изменить фамилию на русском языке.', show_alert=True)
    await callback.message.answer('Вы выбрали изменить фамилию на русском языке.')

# Отмена состояния пользователя по команде Отмена
@router.callback_query(F.data == 'cancel')
async def cancel_heandler(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    message = callback.message
    current_state = await  state.get_state()
    await delete_all_previous_messages(message.chat.id, state, bot)
    if current_state is None:
        return
    await state.clear()
    await send_typing_and_message(
        message.chat.id, bot,
        f'Регистрация прервана.',
        state, reply_markup=kb.main
    )
    await asyncio.sleep(3)
    await delete_all_previous_messages(message.chat.id, state, bot)

# Отмена состояния пользователя по тексту Отмена
@router.message(StateFilter('*'), Command("отмена"))
@router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_heandler_text(message: types.Message, state: FSMContext, bot: Bot) -> None:
    current_state = await  state.get_state()
    await mes_user_history(message, state)
    await delete_all_previous_messages(message.chat.id, state, bot)
    if current_state is None:
        return

    await send_typing_and_message(
        message.chat.id, bot,
        f'Регистрация прервана.',
        state, reply_markup=kb.main
    )
    await asyncio.sleep(3)
    await delete_all_previous_messages(message.chat.id, state, bot)
    await state.clear()



# Возвращение на шаг назад по машине состояний
@router.callback_query(F.data == 'back')
@router.message(StateFilter('*'), Command("назад"))
@router.message(StateFilter('*'), F.text.casefold() == "назад")
async def cancel_heandler(message: types.Message, state: FSMContext) -> None:

    current_state = await  state.get_state()
    # print(current_state)
    if current_state == Register.nameRU:
        await message.answer('Предыдущего шага нет.\nВведите  ФИО на русском или отмените полностью регистрацию и напишите "отмена"')
        return
    if current_state == Register.mailcontact:
        await message.answer('Возвращаемся к вводу ФИО.\nВведите  ФИО на русском или отмените полностью регистрацию и напишите "отмена"')
        await state.set_state(Register.nameRU)
        return
    if current_state == Register.tel:
        await message.answer('Возвращаемся к вводу контактной информации.\nВведите  ваши контакты или отмените полностью регистрацию и напишите "отмена"')
        await state.set_state(Register.mailcontact)
        return
    if current_state == Register.role:
        await message.answer('Возвращаемся к вводу телефона.\nВведите  телефон или отмените полностью регистрацию и напишите "отмена"')
        await state.set_state(Register.tel)
        return
    if current_state == Register.photofile1:
        await message.answer('Возвращаемся к выбору роли.\nВыберите вновь вашу роль на проекте или отмените полностью регистрацию и напишите "отмена".')
        await state.set_state(Register.role)
        return
    if current_state == Register.photofile2:
        await message.answer('Возвращаемся отправке первой фотографии.\n тправьте файл с первой камеры или отмените полностью регистрацию и напишите "отмена"')
        await state.set_state(Register.photofile1)
        return
    if current_state == Register.photofile3:
        await message.answer('Возвращаемся отправке второй фотографии.\nОтправьте файл со второй камеры или отмените полностью регистрацию и напишите "отмена"')
        await state.set_state(Register.photofile2)
        return
    if current_state == Register.verify:
        await message.answer('Возвращаемся отправке третьей фотографии.\nОтправьте файл с третьей камеры или отмените полностью регистрацию и напишите "отмена"')
        await state.set_state(Register.photofile3)
        return

    previous = None
    for step in Register.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await  message.answer(f'Ок, вы вернулись к прошлому шагу \n {Register.texts[previous.state]}')
            return
        previous = step


# Вопросы для регистрации пользователя

#Тестирую удаление всех сообщений, оставил прошлую версию
# @router.message(StateFilter(None), Command('register'))
# async def register(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer('Начнём регистрацию.')
#     await asyncio.sleep(1)
#     await state.set_state(Register.nameRU)
#     new_message = await message.answer('Введите ваше ФИО на русском языке', reply_markup=ReplyKeyboardRemove())
#     await state.update_data(last_bot_message_id=new_message.message_id)

# @router.message(DialogState.active)
# async def handle_dialog(message: types.Message, state: FSMContext):
#     # Добавляем сообщение пользователя в историю
#     data = await state.get_data()
#     history = data["message_history"] + [message.message_id]
#
#     # Удаляем ВСЕ предыдущие сообщения
#     await delete_all_previous_messages(message.chat.id, state)
#     # Показываем анимацию печати
#     await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
#     await asyncio.sleep(1)
#     # Отправляем новое сообщение бота
#     new_msg = await message.answer(f"✅ Принято: {message.text}")
#     # Обновляем историю только новым сообщением бота
#     await state.update_data(message_history=[new_msg.message_id])


@router.message(Register.nameRU)
async def register_nameRU(message: Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    try:
        if not await vl.validate_name_ru(message.text):
            raise vl.ValidationError("Недопустимые символы в имени, исправьте и введите корректно имя")
    except vl.ValidationError as e:
        await send_typing_and_message(message.chat.id, bot, str(e), state)
        return  # Прерываем выполнение функции, если валидация не прошла

    # if not re.match(r"^[А-Яа-яЁё\-\' ]+$", message.text):
    #     return await send_typing_and_message(
    #         message.chat.id, bot,
    #         "Недопустимые символы в имени, исправьте и введите корректно имя",
    #         state)

    # Если валидация прошла успешно, продолжаем обработку
    try:
        # Используем await для вызова асинхронных функций
        nameRU = await vl.format_fio(message.text)
        nameEN = await vl.transliterate_name(message.text)
        initials = await vl.generate_initials(nameEN)  # Используем generate_initials вместо validate_initials

        await state.update_data(
            nameRU=nameRU,
            tg_id=message.from_user.id,
            nameEN=nameEN,
            idn=initials,
        )
    except vl.ValidationError as e:
        await send_typing_and_message(message.chat.id, bot, f"Ошибка при обработке имени: {str(e)}", state)
        return  # Прерываем выполнение функции, если возникла ошибка

    # Удаляем ВСЕ предыдущие сообщения
    await delete_all_previous_messages(message.chat.id, state, bot)

    # Отправляем новое сообщение
    await send_typing_and_message(
        message.chat.id, bot,
        f"✅ Принято: {nameRU}\n\n"
        f"🪪 Ваше имя RU: {nameRU}\n"
        f"🪪 Ваше имя EN: {nameEN}\n"
        f"🪪 Ваши Инициалы: {initials}\n\n"
        f"📫 Введите Контакты для связи (почта или соцсети):",
        state, reply_markup=kb.back_cancel
    )
    await state.set_state(Register.mailcontact)

#Тестирую удаление всех сообщений, оставил прошлую версию
# @router.message(Register.nameRU)
# async def register_nameRU(message: Message, state: FSMContext, bot: Bot):
#     if not re.match(r"^[А-Яа-яЁё\-\' ]+$", message.text):
#         return await message.answer("Недопустимые символы в имени, исправьте и введтие корректно имя")
#     else:
#         nameRU = await registr_fio(message.text)
#         nameEN = await transliterate_russian_to_eng(message.text)
#         initials = await get_initials(nameEN)
#         await state.update_data(nameRU=nameRU, tg_id=message.from_user.id, nameEN=nameEN, idn=initials)
#         data = await state.get_data()
#         last_bot_message_id = data.get("last_bot_message_id")
#         if last_bot_message_id:
#             await delete_message_safe(message.chat.id, last_bot_message_id, bot)
#         # Удаляем сообщение пользователя
#         await delete_message_safe(message.chat.id, message.message_id, bot)
#         # Показываем анимацию "печатается"
#         await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
#         await asyncio.sleep(1)  # Имитация задержки печати
#         # Отправляем новое сообщение
#         new_message = await message.answer(
#             f'Ваше имя RU: {nameRU}\n'
#             f'Ваше имя EN: {nameEN}\n'
#             f'Ваши 🪪 Инициалы: {initials}\n\n'
#             f'Введите 📫 Контакты  по которым с вами можно связаться, почта или социальные сети'
#         )
#         # Обновляем message_id последнего сообщения бота в состоянии
#         await state.update_data(last_bot_message_id=new_message.message_id)
#         await state.set_state(Register.mailcontact)
#

#-----------------------------------------------------------------------------------------------------------------------
# @router.message(Register.nameEN)
# async def register_nameEN(message: Message, state: FSMContext):
#     await state.update_data(nameEN=message.text)
#     await state.set_state(Register.idn)
#     await message.answer('Введите ваши 🪪 Инициалы на латинице, они будут подставленны в имя файла ваших фотографий, как пример вот так KNA')
#
#
# @router.message(Register.idn)
# async def register_idn(message: Message, state: FSMContext):
#     # Очищаем ввод от всех символов, кроме букв, и приводим к верхнему регистру
#     clean_idn = re.sub(r'[^A-Za-z]', '', message.text).upper()
#     # Проверяем длину и наличие только букв
#     if len(clean_idn) != 3:
#         await message.answer(
#             "❌ 🪪 Инициалы должны состоять ровно из трёх латинских букв.\n"
#             "Пример: KNA\nПопробуйте ещё раз:"
#         )
#         return  # Оставляем пользователя в состоянии Register.idn
#
#     # Сохраняем очищенные данные
#     await state.update_data(idn=clean_idn)
#     await state.set_state(Register.mailcontact)
#     await message.answer('Введите 📫 Контакты  по которым с вами можно связаться, почта или социальные сети')
#-----------------------------------------------------------------------------------------------------------------------

@router.message(Register.mailcontact)
async def register_mailcontact(message: Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    await delete_all_previous_messages(message.chat.id, state, bot)
    await state.update_data(mailcontact=message.text)

    # # Удаляем сообщение пользователя
    # await delete_message_safe(message.chat.id, message.message_id, bot)
    # # Показываем анимацию "печатается"
    # await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    # await asyncio.sleep(1)  # Имитация задержки печати
    # Отправляем новое сообщение
    data = await state.get_data()
    await send_typing_and_message(
        message.chat.id, bot,
        f"✅ Принято: {message.text}\n\n"
        f'🪪 Ваше имя RU: {data["nameRU"]}\n'
        f'🪪 Ваше имя EN: {data["nameEN"]}\n'
        f'🪪 Ваши Инициалы: {data["idn"]}\n'
        f'📫 Ваши Контакты: {data["mailcontact"]}\n\n'
        f'☎️ Поделитесь своим Телефоном нажав на кнопку ниже.',
        state, reply_markup=kb.get_tel
    )
    await state.set_state(Register.tel)


# @router.message(Register.tel, F.contact)
# async def get_contact(message: Message, state: FSMContext):
#     phone = message.contact.phone_number
#     await message.answer(f"Номер из контакта: {phone}", reply_markup=types.ReplyKeyboardRemove())
#     await state.update_data(tel=phone)
#     await state.set_state(Register.role)
#     await message.answer('Спасибо',reply_markup=ReplyKeyboardRemove())
#     await message.answer('Выберите вашу роль, фотограф или редактор', reply_markup=await kb.roles())
#
# @router.message(Register.tel, F.text)
# async def validate_phone(message: Message):
#     # Нормализация номера
#     phone = re.sub(r'[^\d]', '', message.text)
#
#     # Проверка российских номеров
#     if len(phone) == 10:
#         phone = f'7{phone}'
#     elif len(phone) == 11 and phone.startswith(('7', '8')):
#         phone = f'7{phone[1:]}'
#
#     if re.match(PHONE_REGEX, message.text) and len(phone) == 12:
#         await message.answer(f"Валидный номер: +{phone}", reply_markup=types.ReplyKeyboardRemove())
#     else:
#         await message.answer("❌ Неверный формат номера. Попробуйте еще раз или используйте кнопку:",
#                              reply_markup=kb.get_tel)

@router.message(Register.tel, F.contact)
async def register_tel(message: Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    phone = message.contact.phone_number
    global edit

    if phone and edit !=1:
        data = await state.get_data()
        await delete_all_previous_messages(message.chat.id, state, bot)
        await state.update_data(tel=phone)
        await send_typing_and_message(
            message.chat.id, bot,
            f"✅ Принято: {phone}\n\n"
            f'Ваше имя RU: {data["nameRU"]}\n'
            f'Ваше имя EN: {data["nameEN"]}\n'
            f'Ваши 🪪 Инициалы: {data["idn"]}\n'
            f'Ваши 📫 Контакты: {data["mailcontact"]}\n'
            f'Ваш номер ☎️ Телефона {phone}\n\n'
            f'Выберите вашу роль, фотограф или редактор',
            state, reply_markup=await kb.roles()
        )
        await state.set_state(Register.role)
    if phone and edit == 1:
        await delete_all_previous_messages(message.chat.id, state, bot)
        await state.update_data(tel=phone)
        data = await state.get_data()
        await send_typing_and_message(
            message.chat.id, bot,
            f'Подтвердите изменения\n'
            f'Ваш новый телефон такой:\n'
            f'☎️ {data["tel"]}',
            state, reply_markup=kb.getphoto
        )
        await state.set_state(Register.verify)
        edit = 0




@router.message(Register.tel, F.text)
async def validate_phone(message: Message, state: FSMContext, bot: Bot):
    global edit
    await mes_user_history(message, state)
    formatted = await vl.format_phone(message.text)
    data = await state.get_data()
    if formatted and edit !=1:
        await delete_all_previous_messages(message.chat.id, state, bot)
        await state.update_data(tel=formatted)
        await send_typing_and_message(
            message.chat.id, bot,
            f"✅ Принято: {formatted}\n\n"
            f'Ваше имя RU: {data["nameRU"]}\n'
            f'Ваше имя EN: {data["nameEN"]}\n'
            f'Ваши 🪪 Инициалы: {data["idn"]}\n'
            f'Ваши 📫 Контакты: {data["mailcontact"]}\n'
            f'Ваш номер ☎️ Телефона {formatted}\n\n'
            f'Выберите вашу роль, фотограф или редактор',
            state, reply_markup=await kb.roles()
        )
        await state.set_state(Register.role)
    elif formatted and edit == 1:
        await delete_all_previous_messages(message.chat.id, state, bot)
        await state.update_data(tel=formatted)
        await state.set_state(Register.verify)
        await send_typing_and_message(
            message.chat.id, bot,
            f'Подтвердите изменения\n'
            f'Ваш новый телефон такой:\n'
            f'☎️ {formatted}',
            state, reply_markup=kb.getphoto
        )
        edit = 0
    else:
        await send_typing_and_message(
            message.chat.id, bot,
            "❌ Неверный формат номера", state, reply_markup=kb.get_tel)
    # else:
    #     await message.answer(f'❌ Неверный формат номера.\n'
    #                          f'Пожалуйста, введите корректный номер ☎️ Телефона в формате +71234567890, или поделитесь контактом нажав на кнопку', reply_markup=kb.get_tel)

#Удаление сообщений пока не нажмётся кнопка с ролью
@router.message(Register.role, ~F.command, )
async def handle_start_state(message: types.Message, bot: Bot):
    if not message.text or not message.text.startswith('/') or not message.text.join('отмена'):
    # """Удаляем все сообщения кроме команд"""
        try:
            # Удаляем сообщение пользователя
            await message.delete()

            # Отправляем уведомление и удаляем его через 4 секунды
            notify = await message.answer("⚠️ Нужно выбрать из предложенных вариантов.")
            await asyncio.sleep(4)
            await notify.delete()

        except Exception as e:
            print(f"Ошибка при обработке сообщения: {e}")


#Если выбрана роль не фотограф
@router.callback_query(Register.role, F.data != 'role_1')
async def select_rol(callback_query: types.CallbackQuery, state: FSMContext,  bot: Bot):
    message = callback_query.message
    role_id = int(callback_query.data.split('_')[1])  # Извлекаем ID роли
    # await mes_user_history(message, state)
    await delete_all_previous_messages(message.chat.id, state, bot)
    #удаляем инлайн клавиатуру по callback_query
    # await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.update_data(role=role_id,
                            photofile1='Не загружена', photofile2='Не загружена', photofile3='Не загружена',
                            serial1='NoSerial', serial2='NoSerial', serial3='NoSerial'
                            )
    data = await state.get_data()
    role = await rq.get_role_name(data["role"])
    await send_typing_and_message(
            message.chat.id, bot,
            f"✅ Принято:  {role}\n\n"
            f'🪪 Ваше имя RU: {data["nameRU"]}\n'
            f'🪪 Ваше имя EN: {data["nameEN"]}\n'
            f'🪪 Ваши Инициалы: {data["idn"]}\n'
            f'📫 Ваши Контакты: {data["mailcontact"]}\n'
            f'☎️ Ваш номер Телефона {data["tel"]}\n'
            f'🪆 Ваша Роль: {role}\n\n'
            f'Спасибо подтвердите отправку данных',
            state, reply_markup=kb.getphoto
        )
    await state.set_state(Register.verify)

#Если выбрали роль Фотограф
@router.callback_query(Register.role, F.data == 'role_1')
async def select_rol(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    message = callback_query.message
    # await mes_user_history(message, state)
    role_id = int(callback_query.data.split('_')[1])  # Извлекаем ID роли
    await delete_all_previous_messages(message.chat.id, state, bot)
    # await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.update_data(role=role_id,
                            photofile1='Не загружена', photofile2='Не загружена', photofile3='Не загружена',
                            serial1='NoSerial', serial2='NoSerial', serial3='NoSerial'
                            )
    data = await state.get_data()
    role = await rq.get_role_name(data["role"])

    await send_typing_and_message(
            message.chat.id, bot,
            f"✅ Принято:  {role}\n\n"
            f'🪪 Ваше имя RU: {data["nameRU"]}\n'
            f'🪪 Ваше имя EN: {data["nameEN"]}\n'
            f'🪪 Ваши Инициалы: {data["idn"]}\n'
            f'📫 Ваши Контакты: {data["mailcontact"]}\n'
            f'☎️ Ваш номер Телефона {data["tel"]}\n'
            f'🪆 Ваша Роль: {role}\n\n'
            f'Спасибо подтвердите отправку данных',
            state, reply_markup=kb.getphoto
        )
    await send_typing_and_message(
        message.chat.id, bot,
        Texts.Messages.PHOTO_FILE,
        state, reply_markup=kb.getphoto
    )
    await state.set_state(Register.photofile1)

# Если отправленны фотогарафии группой, то выполняется этот
@router.message(Register.photofile1, F.content_type.in_({ContentType.DOCUMENT, ContentType.PHOTO}), F.media_group_id)
async def handle_media_group(message: Message, bot: Bot, state: FSMContext):
    media_group_id = message.media_group_id
    username = message.from_user.username
    data = await state.get_data()
    await send_typing_and_message(
        message.chat.id, bot,
        f'Обрабатываю...',
        state
    )
    await mes_user_history(message, state)
    try:
        if media_group_id not in media_groups_cache:
            media_groups_cache[media_group_id] = {
                "username": username,
                "documents": [],
                "processed": False,
                "invalid": False
            }

        group_data = media_groups_cache[media_group_id]

        if group_data["processed"] or group_data["invalid"]:
            return

        # Добавляем файл в группу
        if message.document:
            document_data = {
                "file_id": message.document.file_id,
                "file_name": message.document.file_name
            }
        elif message.photo:
            document_data = {
                "file_id": message.photo[-1].file_id,
                "file_name": None
            }
        group_data["documents"].append(document_data)

        # Проверяем лимит в 3 файла
        if len(group_data["documents"]) > 3:
            group_data["invalid"] = True
            await message.answer("❌ Максимум 3 файла в группе!")
            return

        await asyncio.sleep(1)

        if not group_data["invalid"] and not group_data["processed"] and data["serial1"] == 'NoSerial':
            group_data["processed"] = True
            saved_files = await process_documents(group_data["documents"], username, bot)

            # Инициализация данных FSM
            fsm_data = {
                "serial1": None,
                "serial2": None,
                "serial3": None,
                "photofile1": 'Не загружена',
                "photofile2": 'Не загружена',
                "photofile3": 'Не загружена'
            }

            results = []
            for i, file_path in enumerate(saved_files):
                if i >= 3:  # Обрабатываем только первые 3 файла
                    break

                serial = await sn.async_get_camera_serial_number(file_path)
                file_name = os.path.basename(file_path)

                # Сохраняем в FSM
                fsm_data[f"serial{i + 1}"] = serial
                fsm_data[f"photofile{i + 1}"] = group_data["documents"][i]["file_id"]
                results.append(f"📁 {file_name}\n🔢 Серийный номер: {serial}")

            # Обновляем FSM
            await state.update_data(fsm_data)
            await send_typing_and_message(
                message.chat.id, bot,
                "\n\n".join(results),
                state
            )
            if i + 1  == 2:
                await send_typing_and_message(
                    message.chat.id, bot,
                    f'Спасибо, вы отправили {i + 1} фотографий, этого достаточно для {i + 1} камер, завершите регистрацию нажав на кнопку внизу.\n\n'
                    f'Если у вас {i + 2} камеры, пришлите еще один файл с третьего фотоаппарата.',
                    state, reply_markup=kb.getphoto)
                await state.set_state(Register.photofile3)
            else:
                await send_typing_and_message(
                    message.chat.id, bot,
                    f'Спасибо, вы отправили {i + 1} фотографий, этого достаточно для {i + 1} камер, завершите регистрацию нажав на кнопку внизу.\n\n'
                    f'Если у вас {i + 2} камеры, свяжитесь с рукводством.',
                    state, reply_markup=kb.getphoto)
                await state.set_state(Register.verify)


    except Exception as e:
        await message.answer(f"⚠️ Ошибка, программист хочет денег: {str(e)}")

    finally:
        if media_group_id in media_groups_cache:
            del media_groups_cache[media_group_id]

@router.message(Register.photofile1, F.document)
async def register_photofile(message: types.Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    await save_document(message, bot)
    serial = await sn.main(message)
    await state.update_data(photofile1=message.document.file_id)
    await state.update_data(serial1=serial)
    await message.answer('Вы отправили один файл.\nОтправьте фотографию  с другой камеры так же файлом, или завершите отправку фотографий '
                         'нажав на кнопку ниже.',
                         reply_markup=kb.getphoto)
    await state.set_state(Register.photofile2)



@router.message(Register.photofile2, F.document)
async def register_photofile(message: types.Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    await save_document(message, bot)
    serial = await sn.main(message)
    await state.update_data(serial2=serial)
    await state.update_data(photofile2=message.document.file_id)
    await state.set_state(Register.photofile3)
    await save_document(message, bot)
    await message.answer('Вы отправили 2 файла.\nВсего принимается 3 файла. Отправьте фотографию  с другой камеры так же файлом, или '
                         'завершите отправку фотографий нажав на кнопку ниже.',
                         reply_markup=kb.getphoto)
    await state.set_state(Register.photofile3)

@router.message(Register.photofile3, F.document)
async def register_photofile(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await mes_user_history(message, state)
    if data["serial3"] == None or data["serial3"] == 'NoSerial':
        await save_document(message, bot)
        serial = await sn.main(message)
        await state.update_data(serial3=serial)
        await state.update_data(photofile3=message.document.file_id)
        await save_document(message, bot)
        await message.answer('Спасибо вы отправили 3 фотографии, этого достаточно',
                             reply_markup=kb.getphoto)
        await state.set_state(Register.verify)
    else:
        await state.set_state(Register.verify)


@router.message(Register.verify, F.document)
async def many_camer(message: types.Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    await delete_all_previous_messages(message.chat.id, state, bot)
    await send_typing_and_message(
        message.chat.id, bot,
        f'У вас что 4 разных фотоаппарата?\n'
        f'Хватит отправлять фотографии!',
        state, reply_markup=kb.getphoto
    )

#Удаление сообщений пока не нажмётся кнопка
@router.message(Register.verify, ~F.command, ~F.text.in_({'🏁 Завершить отправку'}))
async def handle_start_state(message: types.Message):
    if not message.text or not message.text.startswith('/') or not message.text.join('отмена'):
    # """Удаляем все сообщения кроме команд"""
        try:
            # Удаляем сообщение пользователя
            await message.delete()

            # Отправляем уведомление и удаляем его через 3 секунды
            notify = await message.answer("⚠️ Работают только кнопки под сообщением.")
            await asyncio.sleep(3)
            await notify.delete()

        except Exception as e:
            print(f"Ошибка при обработке сообщения: {e}")

# Отвечаем на документ его ID
# @router.message(F.document)
# async def get_document(message: Message):
#     await message.answer(f'ID документа: {message.document.file_id}')

@router.message(Register.verify, F.text == '🏁 Завершить отправку')
@router.message(Register.photofile1, F.text == '🏁 Завершить отправку')
@router.message(Register.photofile2, F.text == '🏁 Завершить отправку')
@router.message(Register.photofile3, F.text == '🏁 Завершить отправку')
async  def verify(message: types.Message, state: FSMContext, bot: Bot):
        await mes_user_history(message, state)
        await delete_all_previous_messages(message.chat.id, state, bot)
        await send_typing_and_message(
            message.chat.id, bot,
            'Спасибо, проверьте ваши данные:',
            state, reply_markup=ReplyKeyboardRemove()
        )

        logging.info(F.data)
        data = await state.get_data()
        role = await rq.get_role_name(data["role"])
        if data["photofile3"]  == 'Не загружена' and data["photofile2"]  == 'Не загружена' and data["photofile1"]  == 'Не загружена':
            await message.answer(
                f'🪪 Ваше имя RU: {data["nameRU"]}\n'
                f'🪪 Ваше имя EN: {data["nameEN"]}\n'
                f'🪪 Ваши Инициалы: {data["idn"]}\n'
                f'📫 Ваши Контакты: {data["mailcontact"]}\n'
                f'☎️ Ваш Телефон: {data["tel"]}\n'
                f'🪆 Ваша Роль: {role}\n\n'
                f'Все верно?', reply_markup=kb.proverka)

        elif data["photofile3"]  == 'Не загружена' and data["photofile2"]  == 'Не загружена':
            await message.answer_document(data["photofile1"])
            await message.answer(
                f'🪪 Ваше имя RU: {data["nameRU"]}\n'
                f'🪪 Ваше имя EN: {data["nameEN"]}\n'
                f'🪪 Ваши Инициалы: {data["idn"]}\n'
                f'📫 Ваши Контакты: {data["mailcontact"]}\n'
                f'☎️ Ваш Телефон: {data["tel"]}\n'
                f'🪆 Ваша Роль: {role}\n'
                f'1️⃣ Серийный номер первой камеры: {data["serial1"]}\n\n'
                f'Все верно?', reply_markup=kb.proverka)

        elif data["photofile3"]  == 'Не загружена':
            await message.answer_document(data["photofile1"])
            await message.answer_document(data["photofile2"])
            await message.answer(
                f'🪪 Ваше имя RU: {data["nameRU"]}\n'
                f'🪪 Ваше имя EN: {data["nameEN"]}\n'
                f'🪪 Ваши Инициалы: {data["idn"]}\n'
                f'📫 Ваши Контакты: {data["mailcontact"]}\n'
                f'☎️ Ваш Телефон: {data["tel"]}\n'
                f'🪆 Ваша Роль: {role}\n'
                f'1️⃣ Серийный номер первой камеры: {data["serial1"]}\n'
                f'2️⃣ Серийный номер второй камеры: {data["serial2"]}\n\n'
                f'Все верно?', reply_markup=kb.proverka)

        else:
            await message.answer_document(data["photofile1"])
            await message.answer_document(data["photofile2"])
            await message.answer_document(data["photofile3"])
            await message.answer(
                f'🪪 Ваше имя RU: {data["nameRU"]}\n'
                f'🪪 Ваше имя EN: {data["nameEN"]}\n'
                f'🪪 Ваши Инициалы: {data["idn"]}\n'
                f'📫 Ваши Контакты: {data["mailcontact"]}\n'
                f'☎️ Ваш Телефон: {data["tel"]}\n'
                f'🪆 Ваша Роль: {role}\n'
                f'1️⃣ Серийный номер первой камеры: {data["serial1"]}\n'
                f'2️⃣ Серийный номер второй камеры: {data["serial2"]}\n'
                f'3️⃣ Серийный номер третьей камеры: {data["serial3"]}\n\n'
                f'Все верно?', reply_markup=kb.proverka)
        await state.set_state(Register.verify)


@router.callback_query(Register.verify, F.data == 'no')
async  def proverka_no(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None)
    await callback.answer('Выберите что изменить.', show_alert=True)
    data = await state.get_data()
    role = await rq.get_role_name(data["role"])
    await callback.message.edit_text(
                f'🪪 Ваше имя RU: {data["nameRU"]}\n🪪 Ваше имя EN: {data["nameEN"]}\n☎️ Ваш Телефон: {data["tel"]}\n'
                f'🪪 Ваши инициалы: {data["idn"]}\n📫 Ваши Контакты: {data["mailcontact"]}\n🪆 Вашу Роль: {role}\n\n'
                f'Все верно?', reply_markup=kb.edit)

#-----------------------------------------------------------------------------------------------------------------------
#   Меню редактирования своих данных
#-----------------------------------------------------------------------------------------------------------------------
@router.callback_query(F.data == 'RU')
async def register_nameRU2(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.set_state(Register.nameRU2)
    await callback_query.message.answer(text='Введите исправления в ваше ФИО на русском языке')

@router.message(Register.nameRU2)
async def register_nameRU2(message: Message, state: FSMContext, bot: Bot):
    await mes_user_history(message, state)
    try:
        if not await vl.validate_name_ru(message.text):
            raise vl.ValidationError("Недопустимые символы в имени, исправьте и введите корректно имя")
    except vl.ValidationError as e:
        await send_typing_and_message(message.chat.id, bot, str(e), state)
        return  # Прерываем выполнение функции, если валидация не прошла
    try:
        # Используем await для вызова асинхронных функций
        nameRU = await vl.format_fio(message.text)
        nameEN = await vl.transliterate_name(message.text)
        initials = await vl.generate_initials(nameEN)  # Используем generate_initials вместо validate_initials

        await state.update_data(
            nameRU=nameRU,
            tg_id=message.from_user.id,
            nameEN=nameEN,
            idn=initials,
        )
    except vl.ValidationError as e:
        await send_typing_and_message(message.chat.id, bot, f"Ошибка при обработке имени: {str(e)}", state)
        return  # Прерываем выполнение функции, если возникла ошибка

    await state.set_state(Register.verify)
    await message.answer('Подтвердите изменения',
                         reply_markup=kb.getphoto)

@router.callback_query(F.data == 'EN')
async def register_nameEN2(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.set_state(Register.nameEN2)
    data = await state.get_data()
    await  callback_query.message.answer(text=f'Вы можете внести исправления в ваше имя на английском языке.\n'
                                              f'Сейчас оно такое: {data["nameEN"]}')

@router.message(Register.nameEN2)
async def register_nameEN2(message: Message, state: FSMContext):
    await state.update_data(nameEN=message.text)
    await state.set_state(Register.verify)
    await message.answer('Подтвердите изменения',
                             reply_markup=kb.getphoto)

@router.callback_query(F.data =='idn')
async  def register_idn2(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.set_state(Register.idn2)
    data = await state.get_data()
    await callback_query.message.answer(text=f'Исправьте ваши 🪪 Инициалы на латинице, они будут подставлены в имя файла ваших фотографий, как пример вот так KNA\n'
                              f'сейчас ваши 🪪 Инициалы такие: Ваши 🪪 Инициалы: {data["idn"]}')
@router.message(Register.idn2)
async  def register_idb2(message: Message, state: FSMContext):
        # Очищаем ввод от всех символов, кроме букв, и приводим к верхнему регистру
        clean_idn = re.sub(r'[^A-Za-z]', '', message.text).upper()
        # Проверяем длину и наличие только букв
        if len(clean_idn) != 3:
            await message.answer(
                "❌ 🪪 Инициалы должны состоять ровно из трёх латинских букв.\n"
                "Пример: KNA\nПопробуйте ещё раз:"
            )
            return  # Оставляем пользователя в состоянии Register.idn

        # Сохраняем очищенные данные
        await state.update_data(idn=clean_idn)
        await state.set_state(Register.verify)
        await message.answer('Подтвердите изменения', reply_markup=kb.getphoto)


@router.callback_query(F.data =='contact')
async  def register_mailcontact2(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.set_state(Register.mailcontact2)
    data = await state.get_data()
    await callback_query.message.answer(text=f'Исправьте ваши Контакты  по которым с вами можно связаться, почта или социальные сети\n'
                              f'сейчас ваши Контакты такие:\n\n📫 {data["mailcontact"]}')

@router.message(Register.mailcontact2)
async  def register_mailcontact2(message: Message, state: FSMContext):
    await state.update_data(mailcontact=message.text)
    await state.set_state(Register.verify)
    data = await state.get_data()
    text = (f"{Texts.Messages.DONE}\n" 
            f'\nСейчас ваши Контакты такие:\n\n📫  {data["mailcontact"]}')
    await message.answer(text, reply_markup=kb.getphoto)

@router.callback_query(F.data =='phone')
async  def edit_tel(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    global edit
    message = callback_query.message
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id,
                                        message_id=callback_query.message.message_id, reply_markup=None)
    data = await state.get_data()
    await mes_user_history(message, state)
    await send_typing_and_message(
        message.chat.id, bot,
        f'📫 Исправьте ваш телефон\n'
             f'сейчас ваш телефон такой:\n☎️ Ваш телефон: {data["tel"]}',
        state, reply_markup=kb.get_tel
    )
    await state.set_state(Register.tel)
    edit = 1


#Возникает ошибка, проверить изменение роли
@router.callback_query(F.data == 'role')
async def select_rol2(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.set_state(Register.role2)
    await callback_query.message.answer(text='Выберите вашу роль на проекте', reply_markup=await kb.roles())

@router.callback_query(Register.role2)
async def select_rol2(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(role=callback_query.data)
    await state.set_state(Register.verify)
    await callback_query.message.answer('Подтвердите изменения', reply_markup=kb.getphoto)
    await state.clear()

# @router.callback_query(F.data =='phone')
# async  def register_tel2(message: Message, state: FSMContext):




#-----------------------------------------------------------------------------------------------------------------------
#   Конец меню редактирования своих данных
#-----------------------------------------------------------------------------------------------------------------------

@router.callback_query(Register.verify, F.data == 'yes')
async def proverka_yes(callback: CallbackQuery, state: FSMContext, bot: Bot):
    message = callback.message
    await delete_all_previous_messages(message.chat.id, state, bot)
    # удаляем инлайн клавиатуру
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None)
    await callback.answer('Вы подтвердили верность данных.', show_alert=True)
    await callback.message.answer('Вы подтвердили верность данных.')
    data = await state.get_data()
    load_dotenv()
    admin = int(os.getenv('ADMIN'))

    if data.get('is_edit'):
        await rq.save_temp_changes(callback.from_user.id, data)
        admin_text = await generate_diff_message(
            await rq.get_item_by_tg_id(callback.from_user.id),
            data
        )

        await bot.send_message(
            chat_id=admin,
            text=f"🛠 Запрос на изменения от @{callback.from_user.username}:\n{admin_text}",
            reply_markup=kb.admin_approval_kb(callback.from_user.id)
        )
        await callback.message.answer("✅ Запрос отправлен администратору")
    else:
        try:
            await rq.set_item(data)
            await fu.number_row(data)
            await callback.message.answer(text=Texts.Messages.REG_SUCCESS, reply_markup=ReplyKeyboardRemove())
            await state.clear()

        except Exception as e:
                await callback.message.answer(
                    f"Ошибка: \n {str(e)}\nОбратитесь к программисту, он денег хочет снова",reply_markup=ReplyKeyboardRemove())
                await state.clear()

# #Записываем в БД пользователя с его id
#     await rq.set_item(data)
#     await state.clear()
    await state.set_state(StartState.active)


# Добавим обработчики для админ-подтверждения:
@router.callback_query(F.data.startswith("approve_"))
async def approve_changes(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    if await rq.apply_temp_changes(user_id):
        await callback.message.edit_text(f"✅ Изменения для {user_id} применены")
        await callback.bot.send_message(user_id, "✅ Ваши изменения утверждены!")
    else:
        await callback.answer("❌ Нет ожидающих изменений")


@router.callback_query(F.data.startswith("reject_"))
async def reject_changes(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    await rq.del_temp_changes(user_id)

    # async with async_session() as session:
    #     await session.execute(delete(TempChanges).where(TempChanges.tg_id == user_id))
    #     await session.commit()

    await callback.message.edit_text(f"❌ Изменения для {user_id} отклонены")
    await callback.bot.send_message(user_id, "❌ Ваши изменения были отклонены")



#=======================================================================================================================
#                                                   ФОТОГРАФ
#=======================================================================================================================

# Обработчик inline-кнопки "расписание"
@router.callback_query(F.data == 'schedule_pers')
async def schedule_pers(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()     # Обязательно отвечаем на callback
    await callback_query.message.answer('Напиши что ты хочешь найти?', reply_markup=kb.find)
    await state.set_state(Find.exclude)



# #Поиск по таблице
# @router.message(F.text.lower() == "расписание")
# async def deepseek(message: Message, state: FSMContext):
#     await message.answer('Напиши что ты хочешь найти?', reply_markup=kb.find)
#     # Устанавливаем состояние ожидания выбора слов исключений
#     await state.set_state(Find.exclude)

# Обработчик нажатий на кнопки инлайн-клавиатуры
@router.callback_query(Find.exclude)
async def process_exclude_words(callback: CallbackQuery, state: FSMContext):
    # Игнорируем невалидные callback_data
    if callback.data not in {'ready', 'clear', 'new', 'all'}:
        await callback.answer("⚠️ Действие недоступно")
        return

    # Подтверждаем обработку callback-запроса
    await callback.answer('Пойду поищу')

    # Инициализируем обе переменные
    exclude_words = []
    include_values = []

    # Определяем список исключений на основе callback_data
    exclude_words = []
    if callback.data == "ready":
        exclude_words = ["", "ОТМЕНА", "СНИМАЮТ"]
    elif callback.data == "clear":
        include_values = ["ОТМЕНА"]
    elif callback.data == "new":
        exclude_words = ["СНЯТО", "ОТМЕНА", "СНИМАЮТ"]
    # Если callback_data == "exclude_none", список исключений останется пустым

    # Сохраняем список исключений в state
    await state.update_data(exclude_words=exclude_words, include_values=include_values)

    # Получаем текущие данные состояния
    data = await state.get_data()
    # Если инициалы уже были установлены (например, через выбор фотографа), используем их
    initials = data.get("initials")

    # Если инициалов нет - получаем из БД
    if not initials:
        # Получаем инициалы из базы данных
        tg_id = callback.from_user.id
        try:
            initials = await rq.get_initials(tg_id)
        except Exception as e:
            await callback.message.answer("🔎 Произошла ошибка при получении инициалов.")
            await state.clear()
            return

    if not initials:
        await callback.message.answer("🔎 Инициалы не найдены в базе данных.")
        await state.clear()
        return

    # Сохраняем инициалы в state
    await state.update_data(initials=initials)

    # # Запрашиваем текст для поиска
    # await callback.message.answer("Напиши свои инициалы")
    await state.set_state(Find.send)
    await find_all_text_code(callback.message, state)  # Вызываем функцию поиска



# # Вывод каждого кода отдельным сообщением
# @router.message(Find.send)
# async def find_all_text_code(message: Message, state: FSMContext):
#     # Получаем список исключений и инициалы из state
#     data = await state.get_data()
#     exclude_words: List[str] = data.get("exclude_words", [])
#     initials: str = data.get("initials", "")
#
#     if not initials:
#         await message.answer("🔎 Инициалы не найдены.")
#         await state.clear()
#         return
#
#         # Выполняем поиск
#     results = await fu.find_all_text_code(prefix=initials, exclude_words=exclude_words)
#
#     # results = await fu.find_all_text_code(prefix=message.text, exclude_words=exclude_words)
#
#     # Дополнительная фильтрация на случай если все above_values стали пустыми
#     filtered_results = [
#         (row, col, val, above)
#         for row, col, val, above in results
#         if any(above)  # Оставляем только записи где есть хотя бы одно значение выше
#     ]
#
#     if not filtered_results:
#         await message.answer("🔎 Ничего не найдено или все результаты не имеют данных выше 😔")
#         await state.clear()
#         return
#
#     labels = ["Время", "Место", "Название"]  # Кастомные названия для строк
#     # Отправляем общее количество результатов
#     await message.answer(f"🔍 Найдено результатов: {len(filtered_results)}")
#
#     # Отправляем каждый результат отдельным сообщением
#     for i, (row, col, value, above) in enumerate(filtered_results, 1):
#         response = (
#             f"📌 Результат {i} из {len(filtered_results)}:\n"
#             # f"📍 Строка: {row} | Колонка: {col}\n" # номер строки из таблицы
#             f"💡 Код съемки: {value}\n"
#         )
#
#         # Добавляем информацию о ячейках выше
#         if above:
#             response += "📚 Съемка:\n"
#             for label, val in zip(labels[-len(above):], reversed(above)):
#                 response += f"   ▫️ {label}: {val}\n"
#         # if any(above):
#         #     response += "⬆️ Выше:\n"
#         #     for label, val in zip(labels, reversed(above)):
#         #         if val:
#         #             response += f"   ▪️ {label}: {val}\n"
#             response += f"✅ Персональный код: {value}\n\n"
#             # Создаем клавиатуру с динамическими параметрами
#             keyboard = await kb.create_task_keyboard(row=row, col=col, code=value)
#             await message.answer(response, reply_markup=keyboard)
#             await asyncio.sleep(0.3)  # Задержка между сообщениями
#
#     await state.clear()


# Новая функция с учётом редактирования Вывод каждого кода отдельным сообщением
@router.message(Find.send)
async def find_all_text_code(message: Message, state: FSMContext):
    data = await state.get_data()
    exclude_words = data.get("exclude_words", [])
    include_values = data.get("include_values", [])
    initials = data.get("initials", "")
    logging.info(f'Инициалы в FSM: {initials}')

    if not initials:
        await message.answer("🔎 Инициалы не найдены.")
        await state.clear()
        return

    try:
        results = await fu.find_all_text_code(
            prefix=initials,
            exclude_words=exclude_words,
            include_values=include_values
        )

        filtered_results = [
            (row, col, val, above)
            for row, col, val, above in results
            if any(above)
        ]

        if not filtered_results:
            await message.answer("🔎 Ничего не найдено")
            await state.set_state(Find.exclude)
            return

        status_msg = await message.answer(f"🔍 Найдено результатов: {len(filtered_results)}")

        # Создаем список для хранения ID сообщений
        message_ids = []

        for i, (row, col, value, above) in enumerate(filtered_results, 1):
            below_value = await fu.get_cell_value(row + 1, col)

            response = (
                f"📌 Результат {i}:\n"
                f"💡 Код: {value}\n"
                f"✅ Статус: {below_value}\n"
                "📚 Детали:\n"
            )

            for label, val in zip(["Время", "Место", "Событие"], reversed(above)):
                response += f"   ▫️ {label}: {val}\n"

            # Сначала отправляем сообщение
            sent_message = await message.answer(response)

            # Создаем клавиатуру с REAL message_id
            keyboard = await kb.create_task_keyboard(
                row=row,
                col=col,
                code=value,
                message_id=sent_message.message_id  # Используем реальный ID
            )

            # Обновляем сообщение с клавиатурой
            await sent_message.edit_reply_markup(reply_markup=keyboard)
            await asyncio.sleep(0.3)

        # Сохраняем ID всех сообщений в state
        await state.update_data(message_ids=message_ids)

    except Exception as e:
        await message.answer(f"⚠️ Ошибка поиска: {str(e)}")

    await state.clear()


# Новая функция для редактирования сообщения после нажатия на кнопку со сменой статуса съемки.
async def update_message_after_change(
        callback: CallbackQuery,
        row: int,
        col: int,
        message_id: int,
        new_value: str
):
    """Обновляет текст сообщения и клавиатуру"""
    try:
        # Получаем обновленные данные
        value = await fu.get_cell_value(row, col)
        below_value = await fu.get_cell_value(row + 1, col)

        # Формируем новый текст
        new_text = (
            f"📌 Результат:\n"
            f"💡 Код съемки: {value}\n"
            f"✅ Статус: {below_value}\n"
        )

        # Обновляем сообщение
        await callback.bot.edit_message_text(
            chat_id=callback.from_user.id,
            message_id=message_id,
            text=new_text,
            reply_markup=await kb.create_task_keyboard(row, col, value, message_id)
        )
    except Exception as e:
        print(f"Error updating message: {e}")

# @router.callback_query(F.data.startswith('done'))
# async def handle_done_callback(callback: CallbackQuery):
#     try:
#         _, row_str, col_str = callback.data.split(':')
#         row = int(row_str)
#         col = int(col_str)
#         # Добавим логирование для отладки
#         print(f"DEBUG: Writing to row={row}, col={col}")
#         # Вызов метода из менеджера
#         result = await fu.write_done(row, col)
#         if result:
#             await callback.answer(result)
#         else:
#             await callback.answer("⚠️ Ошибка записи в таблицу")
#     except ValueError:
#         await callback.answer("⚠️ Некорректные данные")
#     except Exception as e:
#         await callback.answer(f"⚠️ Системная ошибка: {str(e)}")
#         print(f"Callback error: {e}")
#
# @router.callback_query(F.data.startswith('cancel'))
# async def handle_done_callback(callback: CallbackQuery):
#     try:
#         _, row_str, col_str = callback.data.split(':')
#         row = int(row_str)
#         col = int(col_str)
#         # # Добавим логирование для отладки
#         # print(f"DEBUG: Writing to row={row}, col={col}")
#         # Вызов метода из менеджера
#         result = await fu.write_cancel(row, col)
#         if result:
#             await callback.answer(result)
#         else:
#             await callback.answer("⚠️ Ошибка записи в таблицу")
#     except ValueError:
#         await callback.answer("⚠️ Некорректные данные")
#     except Exception as e:
#         await callback.answer(f"⚠️ Системная ошибка: {str(e)}")
#         print(f"Callback error: {e}")
#
# @router.callback_query(F.data.startswith('code'))
# async def handle_done_callback(callback: CallbackQuery):
#     try:
#         _, row_str, col_str = callback.data.split(':')
#         row = int(row_str)
#         col = int(col_str)
#         # # Добавим логирование для отладки
#         # print(f"DEBUG: Writing to row={row}, col={col}")
#         # Вызов метода из менеджера
#         result = await fu.write_state(row, col)
#         if result:
#             await callback.answer(result)
#         else:
#             await callback.answer("⚠️ Ошибка записи в таблицу")
#     except ValueError:
#         await callback.answer("⚠️ Некорректные данные")
#     except Exception as e:
#         await callback.answer(f"⚠️ Системная ошибка: {str(e)}")
#         print(f"Callback error: {e}")
#
# @router.callback_query(F.data.startswith('error'))
# async def handle_done_callback(callback: CallbackQuery):
#     try:
#         _, row_str, col_str = callback.data.split(':')
#         row = int(row_str)
#         col = int(col_str)
#         # # Добавим логирование для отладки
#         # print(f"DEBUG: Writing to row={row}, col={col}")
#         # Вызов метода из менеджера
#         result = await fu.write_error(row, col)
#         if result:
#             await callback.answer(result)
#         else:
#             await callback.answer("⚠️ Ошибка записи в таблицу")
#     except ValueError:
#         await callback.answer("⚠️ Некорректные данные")
#     except Exception as e:
#         await callback.answer(f"⚠️ Системная ошибка: {str(e)}")
#         print(f"Callback error: {e}")

# Обновлённые 4 функции для редактирования статуса съемки после нажатия на кнопу
# @router.callback_query(F.data.startswith('done'))
# async def handle_done_callback(callback: CallbackQuery):
#     try:
#         _, row_str, col_str, message_id_str  = callback.data.split(':')
#         row = int(row_str)
#         col = int(col_str)
#         message_id = int(message_id_str)
#
#         # Добавим логирование для отладки
#         print(f"DEBUG: Writing to row={row}, col={col}")
#         # Выполняем запись
#         result_msg, new_value = await fu.write_done(row, col)
#
#         if result_msg and new_value:
#             await update_message_after_change(callback, row, col, message_id, new_value)
#             await callback.answer(result_msg)
#         else:
#             await callback.answer("⚠️ Ошибка записи в таблицу")
#
#     except Exception as e:
#         await callback.answer(f"⚠️ Ошибка: {str(e)}")
#         print(f"Callback error: {e}")
#
#
#
# @router.callback_query(F.data.startswith('cancel'))
# async def handle_done_callback(callback: CallbackQuery):
#     try:
#         _, row_str, col_str, message_id_str = callback.data.split(':')
#         row = int(row_str)
#         col = int(col_str)
#         message_id = int(message_id_str)
#
#         # Добавим логирование для отладки
#         print(f"DEBUG: Writing to row={row}, col={col}")
#         # Выполняем запись
#         result_msg, new_value = await fu.write_cancel(row, col)
#
#         if result_msg and new_value:
#             await update_message_after_change(callback, row, col, message_id, new_value)
#             await callback.answer(result_msg)
#         else:
#             await callback.answer("⚠️ Ошибка записи в таблицу")
#
#     except Exception as e:
#         await callback.answer(f"⚠️ Ошибка: {str(e)}")
#         print(f"Callback error: {e}")
#
# @router.callback_query(F.data.startswith('code'))
# async def handle_done_callback(callback: CallbackQuery):
#     try:
#         _, row_str, col_str, message_id_str = callback.data.split(':')
#         row = int(row_str)
#         col = int(col_str)
#         message_id = int(message_id_str)
#
#         # Добавим логирование для отладки
#         print(f"DEBUG: Writing to row={row}, col={col}")
#         # Выполняем запись
#         result_msg, new_value = await fu.write_state(row, col)
#
#         if result_msg and new_value:
#             await update_message_after_change(callback, row, col, message_id, new_value)
#             await callback.answer(result_msg)
#         else:
#             await callback.answer("⚠️ Ошибка записи в таблицу")
#
#     except Exception as e:
#         await callback.answer(f"⚠️ Ошибка: {str(e)}")
#         print(f"Callback error: {e}")
#
# @router.callback_query(F.data.startswith('error'))
# async def handle_done_callback(callback: CallbackQuery):
#     try:
#         _, row_str, col_str, message_id_str = callback.data.split(':')
#         row = int(row_str)
#         col = int(col_str)
#         message_id = int(message_id_str)
#
#         # Добавим логирование для отладки
#         print(f"DEBUG: Writing to row={row}, col={col}")
#         # Выполняем запись
#         result_msg, new_value = await fu.write_error(row, col)
#
#         if result_msg and new_value:
#             await update_message_after_change(callback, row, col, message_id, new_value)
#             await callback.answer(result_msg)
#         else:
#             await callback.answer("⚠️ Ошибка записи в таблицу")
#
#     except Exception as e:
#         await callback.answer(f"⚠️ Ошибка: {str(e)}")
#         print(f"Callback error: {e}")


@router.callback_query(F.data.startswith('done'))
async def handle_done_callback(callback: CallbackQuery):
    await handle_status_update(callback, "СНЯТО")

@router.callback_query(F.data.startswith('cancel'))
async def handle_cancel_callback(callback: CallbackQuery):
    await handle_status_update(callback, "ОТМЕНА")

@router.callback_query(F.data.startswith('code'))
async def handle_code_callback(callback: CallbackQuery):
    await handle_status_update(callback, "СНИМАЮТ")

@router.callback_query(F.data.startswith('error'))
async def handle_error_callback(callback: CallbackQuery):
    await handle_status_update(callback, "")

async def handle_status_update(callback: CallbackQuery, status: str):
    try:
        # Правильно парсим callback_data
        _, row_str, col_str, msg_id = callback.data.split(':')
        row = int(row_str)
        col = int(col_str)
        target_message_id = int(msg_id)  # Это ключевое изменение

        # Обновляем ячейку в таблице
        result = None
        if status == "СНЯТО":
            result = await fu.write_done(row, col)
        elif status == "ОТМЕНА":
            result = await fu.write_cancel(row, col)
        elif status == "СНИМАЮТ":
            result = await fu.write_state(row, col)
        else:
            result = await fu.write_error(row, col)

        if not result:
            await callback.answer("⚠️ Ошибка обновления")
            return

        # Получаем актуальные данные
        current_code = await fu.get_cell_value(row, col)
        current_status = await fu.get_cell_value(row + 1, col)
        above_values = await fu.get_above_values(row, col, 3)

        # Формируем новый текст
        new_text = (
            f"📌 Записали ответ\n"
            f"💡 Код: {current_code}\n"
            f"✅ Статус: {current_status}\n"
            "📚 Детали:\n"
        )
        for label, val in zip(["Время", "Место", "Событие"], (above_values)):
            if val:  # Добавляем только непустые значения
                new_text += f"   ▫️ {label}: {val}\n"

        # Редактируем целевое сообщение
        await callback.bot.edit_message_text(
            chat_id=callback.from_user.id,
            message_id=target_message_id,  # Используем целевой ID
            text=new_text,
            reply_markup=None
        )
        await callback.answer(f"✅ Статус обновлен: {status}")

    except Exception as e:
        await callback.answer(f"⚠️ Ошибка: {str(e)}")
        print(f"Error in handle_status_update: {e}")


# # Вывод одним сообщением точного совпадения из поиска по таблице
# @router.message(Find.send)
# async def find_cod(message: Message, state: FSMContext):
#     result = await fu.find_text_code(text=message.text)
#
#     if not result:
#         await message.answer("Ничего не найдено 😔")
#         await state.clear()
#         return
#
#     response = "🔍 Вот что я нашел:\n\n"
#     labels = ["Время", "Место", "Название"]  # Кастомные названия для строк
#
#     for row, col, value, above in result:
#         response += f"📍 Координаты: строка {row}, колонка {col}\n\n"
#
#         # Фильтруем пустые значения и добавляем кастомные названия
#         filtered_above = [
#             (label, val)
#             for label, val in zip(labels, reversed(above))
#             if val.strip()
#         ]
#
#         if filtered_above:
#             response += "📌 Связанные данные:\n"
#             for label, val in filtered_above:
#                 response += f"   ▫️ {label}: {val}\n"
#
#         response += f"✅ Персональный код: {value}\n\n"
#
#     await message.answer(response.strip())
#     await state.clear()


# @router.message(Find.send)
# async def find_cod(message: Message, state: FSMContext):
#     result = await fu.find_text_code(text=message.text)
#     for row, col, value, above in result:
#         await message.answer(f'Вот что я нашел:')
#         for i, val in enumerate(reversed(above), start=1):
#             await message.answer(f'{val}')
#         await message.answer(f'{value}')
#     await state.clear()

# @router.message(Find.send)
# async def find_text(message: Message, state: FSMContext):
#     result = await fu.find_text_in_sheet(text=message.text)
#     await message.answer(f'Вот что я нашел: {result}')
#     await state.clear()


##======================================================================================================================
##                                                   БИЛД-РЕДАКТОР
##======================================================================================================================
#=======================================================================================================================
# Функция сохранения данных в TSV по сообщению Файл. Дописать на нажатие кнопки и выбор, что сохранить первую страницу
# или лист ПУТЬ.
#=======================================================================================================================

@router.callback_query(F.data.in_({"tables_day", "tables_dist"}))  # Обрабатываем два callback_data
async def handle_report_request(callback_query: types.CallbackQuery, bot: Bot):
    await callback_query.answer()
    tg_id = callback_query.from_user.id
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    temp_filename = f"TSV/report_{tg_id}_{timestamp}.tsv"

    try:
        role = await rq.get_role(tg_id)
        logging.info(f"Получена роль: {role}")  # Логируем значение role
        # Преобразуем role в строку для сравнения
        if str(role) == "2":  # Сравниваем со строкой "2"
            # Создаем директорию для отчетов если ее нет
            Path("TSV").mkdir(exist_ok=True)

            # Определяем, какой лист нужно сохранить
            if callback_query.data == "tables_day":
                sheet_name = None  # Используем лист по умолчанию
            elif callback_query.data == "tables_dist":
                sheet_name = "ПУТЬ"  # Используем лист "ПУТЬ"


            # Сохраняем отчет
            await callback_query.answer("🔄 Начинаю сохранение файла...")
            success, sheet_title = await fu.save_sheet_as_tsv(
                filename=temp_filename,
                sheet_name=sheet_name  # Передаем имя листа
            )

            # Генерируем безопасное имя файла
            safe_title = re.sub(r'[\\/*?:"<>|]', '', sheet_title).replace(' ', '_')
            # output_filename = f"{safe_title}_{timestamp}.tsv" # файл с именем лист_время
            output_filename = f"{safe_title}_{timestamp}.tsv" # файл с именем Лист

            # Отправляем файл
            # Чтение файла в "rb" бинарном режиме необходимо для корректной работы.
            with open(temp_filename, "rb") as file:
                await bot.send_document(
                    chat_id=tg_id,
                    document=types.BufferedInputFile(
                        file=file.read(),
                        filename=output_filename
                    ),
                    caption=f"✅ Файл '{sheet_title}' готов!"
                )

            # Удаляем временный файл
            Path(temp_filename).unlink(missing_ok=True)
        else:
            await callback_query.answer("🔄 Вам не нужен этот файл")

    except Exception as e:
        await callback_query.answer(f"❌ Ошибка при сохранении файла: {str(e)}")
        print(f"Error: {str(e)}")
#=======================================================================================================================
# Конец Функция сохранения данных в TSV по сообщению Файл. Дописать на нажатие кнопки и выбор, что сохранить первую страницу
# или лист ПУТЬ.
#=======================================================================================================================

#=======================================================================================================================
# Обработка нажатий на кнопку билд-редатора Все фотографы
#=======================================================================================================================
# Обработчик кнопки "Все фотографы"
@router.callback_query(F.data == 'all_photographers', StateFilter(None))
async def all_photographers_handler(callback: CallbackQuery):
    await callback.answer()
    keyboard = await kb.photographers_keyboard()
    await callback.message.answer(
        "📸 Список фотографов:",
        reply_markup=keyboard
    )


# Обработчик выбора фотографа
@router.callback_query(F.data.startswith('photographer_'))
async def photographer_selected(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # Сбрасываем возможные предыдущие состояния
    idn = callback.data.split('_')[1]
    # Полностью обновляем состояние, сохраняя только инициалы
    await state.set_data({
        "initials": idn  # Сбрасываем фильтры при новом выборе
    })

    await callback.message.answer(
        "🔎 Выберите какие съемки показать:",
        reply_markup=kb.find
    )
    await state.set_state(Find.exclude)
    await callback.answer()
#=======================================================================================================================
# Обработка нажатий на кнопку билд-редатора Все фотографы
#=======================================================================================================================

#=======================================================================================================================
# обработчик для кнопки "🔍 Поиск кода"
#=======================================================================================================================
@router.callback_query(F.data == 'search_code', StateFilter(None))
async def handle_search_code(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Find.wait)
    await callback.message.answer(
        "🔍 Введите точный код для поиска (например: KNA1001):",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Find.wait, F.text)
async def process_search_code(message: Message, state: FSMContext):
    search_text = message.text.strip()
    await state.update_data(search_text=search_text)

    try:
        # Используем функцию для точного поиска
        results = await fu.find_text_code(
            text=search_text,
            spreadsheet_name="Архипелаг 2024",
            sheet_name="Расписание фото"
        )

        if not results:
            await message.answer("🔎 Совпадений не найдено")
            await state.clear()
            return

        await message.answer(f"🔍 Найдено совпадений: {len(results)}")

        for i, (row, col, value, above) in enumerate(results, 1):
            # Получаем текущий статус из ячейки ниже
            current_status = await fu.get_cell_value(row + 1, col)

            response = (
                f"📌 Результат {i}:\n"
                f"💡 Код: {value}\n"
                f"✅ Текущий статус: {current_status}\n"
                "📚 Контекст:\n"
            )

            # Добавляем данные из ячеек выше
            for label, val in zip(["Время", "Место", "Событие"], reversed(above)):
                if val: response += f"   ▫️ {label}: {val}\n"

            # Отправляем сообщение с клавиатурой
            sent_message = await message.answer(response)
            keyboard = await kb.create_task_keyboard(
                row=row,
                col=col,
                code=value,
                message_id=sent_message.message_id
            )
            await sent_message.edit_reply_markup(reply_markup=keyboard)
            await asyncio.sleep(0.3)

    except Exception as e:
        await message.answer(f"⚠️ Ошибка при поиске: {str(e)}")

    await state.clear()