# from email.policy import default
# from sys import exception
import phonenumbers
import Texts
import os
import re
import asyncio

from phonenumbers import NumberParseException, PhoneNumberFormat
from aiogram import F, Router, types, Bot
# from aiogram.client.default import Default
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
# from aiogram.methods import SendMessage, ForwardMessage
from aiogram.enums import ContentType, ChatAction
#Импортировали тексты из отдельного файла
from Texts import Messages, Buttons, StatesText



import app.keyboards as kb
import app.database.requests as rq
import app.Sheets.function as fu
import app.SerialNumber as sn

from aiogram.utils.formatting import PhoneNumber
from app.database.requests import get_item
from requests import session

#from aiohttp.web_fileresponse import content_type
#from google.auth import message

#Объект класса router Router
router = Router()

class StartState(StatesGroup):
    active = State()  # Состояние, в котором будем удалять сообщения


class Register(StatesGroup):
    last_bot_message_id = State()
    tg_id = State()
    nameRu = State()
    nameEn = State()
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
    verefy = State()
    nameRu2 = State()
    nameEn2 = State()
    idn2 = State()
    mailcontact2 = State()
    tel2 = State()
    role2 = State()
    texts = StatesText.REGISTER

# Переменная для хранения message_id последнего сообщения бота
last_bot_message_id = None

@router.message(CommandStart())
# асинхронная функция cmd_start которая принимает в себя объект Massage
async def cmd_start(message: Message, state: FSMContext):
# внутри функции cmd_start обращаемся к методу answer, он позволяет отвечать этому же пользователю
#     await message.answer('Привет!', reply_markup=kb.main)
# отправляем на команлу старт фотографию с подписью и клавиатуру main
#     await  state.clear()
    await state.set_state(StartState.active)
    await message.answer_photo(photo='AgACAgIAAxkBAAPgZ361se9D_xn8AwRI7Y1gBmdmTiwAAgfrMRsQmvlLUMXQ9_Z9HXABAAMCAAN5AAM2BA',
                               caption=Messages.START.format(name=message.from_user.full_name), reply_markup=kb.main)
    await message.answer(
        "Вы в режиме самого начала. Все сообщения кроме команд будут удаляться!\n"
        "Доступные команды:\n"
        "/help - справка\n"
        "/register - регистрация"
    )
# отправляем методом ответа на сообщение стикер по его ID
#     await message.reply_sticker(sticker='CAACAgIAAxkBAAPYZ36b1AUNHQg55cEEfzilVTX1lCYAArkRAAJClVFLVmGP6JmH07A2BA', reply_markup=ReplyKeyboardRemove())
# Получаем ID пользователя и Имя из самого первого сообщения
#    await message.reply(f'Привет :) \nТвой ID: {message.from_user.id}\nИмя: {message.from_user.first_name}\n'
#                        f'Фамилия: {message.from_user.last_name}\nНик: @{message.from_user.username}')
#
# Записываем в БД пользоватлея с его id
    await rq.set_user(message.from_user.id)
#   await message.reply('Как дела?')

@router.message(Command('help'))
async def  cmd_help(message: Message):
    await message.answer('Вы попали в раздел помощи 😴😱😜😂😝')

@router.message(StateFilter('*'), Command('register'))
async def register(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Начнём регистрацию.')
    # await asyncio.sleep(1)

    # Инициализируем историю сообщений
    await state.update_data(message_history=[])
    # Отправляем первое сообщение и добавляем его в историю
    msg = await message.answer('Введите ваше ФИО на русском языке', reply_markup=ReplyKeyboardRemove())
    await state.update_data(message_history=[msg.message_id])
        # Активируем состояние диалога
    await state.set_state(Register.nameRu)

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

# Функция для безопасного удаления списка сообщений
async def delete_message_safe(chat_id: int, message_id: int, bot: Bot):
    """Безопасное удаление одного сообщения"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

async def delete_all_previous_messages(chat_id: int, state: FSMContext, bot: Bot):
    """Удаление всех сообщений из истории и очистка хранилища"""
    data = await state.get_data()
    messages_to_delete = data.get("message_history", [])
    # Удаляем все сообщения из истории
    for msg_id in messages_to_delete:
        await delete_message_safe(chat_id, msg_id, bot)
    # Очищаем историю
    await state.update_data(message_history=[])

# Функция для безопасного удаления последнего сообщения
async def delete_message_safe(chat_id, message_id, bot: Bot):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")

# Функция валидации номера телефона
async def format_phone(phone: str) -> str:
    try:
        parsed = phonenumbers.parse(phone, "RU")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        return None
    except NumberParseException:
        return None

#Функция получения инициалов
async def get_initials(nameEn: str) -> str:
    return ''.join([part[0].upper() for part in nameEn.split() if part])

#Функция перевода в латиницу
async def transliterate_russian_to_eng(name_ru: str) -> str:
    """
    Транслитерирует русские ФИО в английские согласно правилам загранпаспортов РФ.
    Пример: 'Иванов Иван Иванович' → 'Ivanov Ivan Ivanovich'
    """
    translit_dict = Texts.Translit_EN.EN
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


#-----------------------------------------------------------------------------------------------------------------------
#Проверяем новые функции
#-----------------------------------------------------------------------------------------------------------------------


@router.message(F.photo)
async def forward_message(message: Message, bot: Bot):
    await bot.forward_message('-1002378314584', message.from_user.id, message.message_id)
    await message.answer(Messages.PHOTO)
# @router.message(F.document)
# async def forward_message(message: Message, bot: Bot):
#     await bot.forward_message('-1002378314584', message.from_user.id, message.message_id)
#     await message.answer('Спасибо что отправили фотографию документом.')

# Получить ID медиа данных
# Отвечаем на стикер его ID и ID чата
# @router.message(F.sticker)
# async def check_sticker(message: Message):
#     await message.answer(f'ID стикера: {message.sticker.file_id}')
#     await message.answer(f'id чата: {message.from_user.id, message.chat.id}')

# # отвечаем на фото его ID
# @router.message(F.photo)
# async def get_photo(message: Message):
#     await message.answer(f'ID фото: {message.photo[-1].file_id}')

# Отвечаем на документ его ID
# @router.message(F.document)
# async def get_document(message: Message):
#     await message.answer(f'ID документа: {message.document.file_id}')

# async def process_document(message: types.Message, bot: Bot):
#     await save_document(message, bot)

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
@router.message(StateFilter('*'), Command("отмена"))
@router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_heandler(message: types.Message, state: FSMContext) -> None:
    current_state = await  state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Отмена регистрации", reply_markup=kb.main)



# Возвращение на шаг назад по машине состояний
@router.message(StateFilter('*'), Command("назад"))
@router.message(StateFilter('*'), F.text.casefold() == "назад")
async def cancel_heandler(message: types.Message, state: FSMContext) -> None:

    current_state = await  state.get_state()
    print(current_state)
    if current_state == Register.nameRu:
        await message.answer('Предыдущего шага нет, введите  ФИО на русском или отмените полностью регистрацию и напишите "отмена"')
        return
    if current_state == Register.mailcontact:
        await message.answer('Возвращаемся к вводу ФИО, введите  ФИО на русском или отмените полностью регистрацию и напишите "отмена"')
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
#     await state.set_state(Register.nameRu)
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

@router.message(Register.nameRu)
async def register_nameRu(message: Message, state: FSMContext, bot: Bot):
    if not re.match(r"^[А-Яа-яЁё\-\' ]+$", message.text):
        return await message.answer("Недопустимые символы в имени, исправьте и введите корректно имя")
    else:
        nameRu = await registr_fio(message.text)
        nameEn = await transliterate_russian_to_eng(message.text)
        initials = await get_initials(nameEn)
        await state.update_data(nameRu=nameRu, tg_id=message.from_user.id, nameEn=nameEn, idn=initials)

        # Добавляем сообщение пользователя в историю
        data = await state.get_data()
        history = data["message_history"] + [message.message_id]
        print(data)

        # Удаляем ВСЕ предыдущие сообщения
        await delete_all_previous_messages(message.chat.id, state, bot)
        # Показываем анимацию печати
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        await asyncio.sleep(1)
        # Отправляем новое сообщение бота
        new_msg = await message.answer(f"✅ Принято: {message.text}")
        # Обновляем историю только новым сообщением бота
        await state.update_data(message_history=[new_msg.message_id])

        # Показываем анимацию "печатается"
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(1)  # Имитация задержки печати
        # Отправляем новое сообщение
        new_message = await message.answer(
            f'Ваше имя RU: {nameRu}\n'
            f'Ваше имя EN: {nameEn}\n'
            f'Ваши инициалы: {initials}\n\n'
            f'Введите контакты  по которым с вами можно связаться, почта или социальные сети'
        )
        # Обновляем message_id последнего сообщения бота в состоянии
        await state.set_state(Register.mailcontact)

#Тестирую удаление всех сообщений, оставил прошлую версию
# @router.message(Register.nameRu)
# async def register_nameRu(message: Message, state: FSMContext, bot: Bot):
#     if not re.match(r"^[А-Яа-яЁё\-\' ]+$", message.text):
#         return await message.answer("Недопустимые символы в имени, исправьте и введтие корректно имя")
#     else:
#         nameRu = await registr_fio(message.text)
#         nameEn = await transliterate_russian_to_eng(message.text)
#         initials = await get_initials(nameEn)
#         await state.update_data(nameRu=nameRu, tg_id=message.from_user.id, nameEn=nameEn, idn=initials)
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
#             f'Ваше имя RU: {nameRu}\n'
#             f'Ваше имя EN: {nameEn}\n'
#             f'Ваши инициалы: {initials}\n\n'
#             f'Введите контакты  по которым с вами можно связаться, почта или социальные сети'
#         )
#         # Обновляем message_id последнего сообщения бота в состоянии
#         await state.update_data(last_bot_message_id=new_message.message_id)
#         await state.set_state(Register.mailcontact)
#

#-----------------------------------------------------------------------------------------------------------------------
# @router.message(Register.nameEn)
# async def register_nameEN(message: Message, state: FSMContext):
#     await state.update_data(nameEn=message.text)
#     await state.set_state(Register.idn)
#     await message.answer('Введите ваши инициалы на латинице, они будут подставленны в имя файла ваших фотографий, как пример вот так KNA')
#
#
# @router.message(Register.idn)
# async def register_idn(message: Message, state: FSMContext):
#     # Очищаем ввод от всех символов, кроме букв, и приводим к верхнему регистру
#     clean_idn = re.sub(r'[^A-Za-z]', '', message.text).upper()
#     # Проверяем длину и наличие только букв
#     if len(clean_idn) != 3:
#         await message.answer(
#             "❌ Инициалы должны состоять ровно из трёх латинских букв.\n"
#             "Пример: KNA\nПопробуйте ещё раз:"
#         )
#         return  # Оставляем пользователя в состоянии Register.idn
#
#     # Сохраняем очищенные данные
#     await state.update_data(idn=clean_idn)
#     await state.set_state(Register.mailcontact)
#     await message.answer('Введите контакты  по которым с вами можно связаться, почта или социальные сети')
#-----------------------------------------------------------------------------------------------------------------------

@router.message(Register.mailcontact)
async def register_mailcontact(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(mailcontact=message.text)
    await state.set_state(Register.tel)
    data = await state.get_data()
    last_bot_message_id = data.get("last_bot_message_id")
    if last_bot_message_id:
        await delete_message_safe(message.chat.id, last_bot_message_id, bot)
    # Удаляем сообщение пользователя
    await delete_message_safe(message.chat.id, message.message_id, bot)
    # Показываем анимацию "печатается"
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(1)  # Имитация задержки печати
    # Отправляем новое сообщение
    new_message = await message.answer(
        f'Ваше имя RU: {data["nameRu"]}\n'
        f'Ваше имя EN: {data["nameEn"]}\n'
        f'Ваши инициалы: {data["idn"]}\n'
        f'Ваши контакты: {data["mailcontact"]}\n\n'
        f'Поделитесь своим телефоном нажав на кнопку ниже.', reply_markup=kb.get_tel
    )
    # Обновляем message_id последнего сообщения бота в состоянии
    await state.update_data(last_bot_message_id=new_message.message_id)



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
async def register_tel(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await message.answer(f"Номер из контакта: {phone}", reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(tel=phone)
    await state.set_state(Register.role)
    await message.answer('Выберите вашу роль, фотограф или редактор', reply_markup=await kb.roles())


@router.message(Register.tel, F.text)
async def validate_phone(message: Message, state: FSMContext):
    formatted = await format_phone(message.text)
    if formatted:
        await message.answer(f"Валидный номер: {formatted}", reply_markup=ReplyKeyboardRemove())
    # phone_text = message.text
    # # Убедиться, что у объекта message.contact есть атрибут 'phone_number'
    # if message.contact and hasattr(message.contact, 'phone_number'):
    #     phone_key = message.contact.phone_number
    # else:
    #     phone_key = None
    # # Проверка на корректный номер телефона с помощью регулярного выражения
    # if re.match(r'^\+7\d{10}$', phone_text or phone_key):
    #     if message.contact:  # Добавлено условие для проверки наличия объекта message.contact
    #         await state.update_data(tel=message.contact.phone_number)
    #     else:
    #         await state.update_data(tel=message.text)
        await state.set_state(Register.role)
        await message.answer('Спасибо',reply_markup=ReplyKeyboardRemove())
        await message.answer('Выберите вашу роль, фотограф или редактор', reply_markup=await kb.roles())
    else:
        await message.answer("❌ Неверный формат номера", reply_markup=kb.get_tel)
        await state.update_data(tel={formatted})
    # else:
    #     await message.answer(f'❌ Неверный формат номера.\n'
    #                          f'Пожалуйста, введите корректный номер телефона в формате +71234567890, или поделитесь контактом нажав на кнопку', reply_markup=kb.get_tel)

#Если выбрана роль не фотограф
@router.callback_query(Register.role, F.data != 'Фотограф')
async def select_rol(callback_query: types.CallbackQuery, state: FSMContext,  bot: Bot):
    #удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.update_data(role=callback_query.data,
                            photofile1='Не загружена', photofile2='Не загружена', photofile3='Не загружена',
                            serial1='NoSerial', serial2='NoSerial', serial3='NoSerial'
                            )
    await state.set_state(Register.verefy)
    await callback_query.message.answer('Спасибо подтвердите отправку данных',
                         reply_markup=kb.getphoto)

#Если выбрали роль Фотограф
@router.callback_query(Register.role, F.data == 'Фотограф')
async def select_rol(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.update_data(role=callback_query.data,
                            photofile1='Не загружена', photofile2='Не загружена', photofile3='Не загружена',
                            serial1='NoSerial', serial2='NoSerial', serial3='NoSerial'
                            )
    await state.set_state(Register.photofile1)
    await callback_query.message.answer('Отправьте по одной фотографии с каждой вашей камеры, обязательно файлом.',
                         reply_markup=kb.getphoto)

# Если отправленны фотогарафии группой то выполняется этот
@router.message(Register.photofile1, F.content_type.in_({ContentType.DOCUMENT, ContentType.PHOTO}), F.media_group_id)
async def handle_media_group(message: Message, bot: Bot, state: FSMContext):
    media_group_id = message.media_group_id
    username = message.from_user.username

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

        await asyncio.sleep(3)

        if not group_data["invalid"] and not group_data["processed"]:
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
            await message.answer("\n\n".join(results))
            await message.answer(f'Спасибо, вы отправили {i + 1} фотографий, этого достаточно, завершите регистрацию нажав на кнопку внизу.', reply_markup=kb.getphoto)

    except Exception as e:
        await message.answer(f"⚠️ Ошибка, программист хочет денег: {str(e)}")

    finally:
        if media_group_id in media_groups_cache:
            del media_groups_cache[media_group_id]

@router.message(Register.photofile1, F.document)
async def register_photofile(message: types.Message, state: FSMContext, bot: Bot):
    await save_document(message, bot)
    serial = await sn.main(message)
    await state.update_data(photofile1=message.document.file_id)
    await state.update_data(serial1=serial)
    await state.set_state(Register.photofile2)
    await message.answer('Вы отправили один файл.\nОтправьте фотографию  с другой камеры так же файлом, или завершите отправку фотографий '
                         'нажав на кнопку ниже.',
                         reply_markup=kb.getphoto)


@router.message(Register.photofile2, F.document)
async def register_photofile(message: types.Message, state: FSMContext, bot: Bot):
    await save_document(message, bot)
    serial = await sn.main(message)
    await state.update_data(serial2=serial)
    await state.update_data(photofile2=message.document.file_id)
    await state.set_state(Register.photofile3)
    await save_document(message, bot)
    await message.answer('Вы отправили 2 файла.\nВсего принимается 3 файла. Отправьте фотографию  с другой камеры так же файлом, или '
                         'завершите отправку фотографий нажав на кнопку ниже.',
                         reply_markup=kb.getphoto)

@router.message(Register.photofile3, F.document)
async def register_photofile(message: types.Message, state: FSMContext, bot: Bot):
    await save_document(message, bot)
    serial = await sn.main(message)
    await state.update_data(serial3=serial)
    await state.update_data(photofile3=message.document.file_id)
    await state.set_state(Register.verefy)
    await save_document(message, bot)
    await message.answer('Спасибо вы отправили 3 фотографии, этого достаточно',
                         reply_markup=kb.getphoto)

@router.message(Register.verefy, F.text == 'Завершить отправку')
async  def verefy(message: types.Message, state: FSMContext, bot: Bot):
        # старый ответ до того как начал принимать фотографии
        await bot.send_message(message.chat.id, 'Спасибо, проверьте ваши данные:', reply_markup=ReplyKeyboardRemove())
        await state.set_state(Register.verefy)
        data = await state.get_data()
        # await message.answer(f'Ваше имя RU: {data["nameRu"]}\nВаше имя EN: {data["nameEn"]}\nВаш телефон: {data["tel"]}\n'
        #                      f'Ваши инициалы: {data["idn"]}\nВаши контакты: {data["mailcontact"]}\nВаша роль: {data["role"]}\n'
        #                      f'Первая фотография: {data["photofile1"]}\nВторая фотография: {data["photofile2"]}\n'
        #                      f'Третья фотография: {data["photofile3"]}\nВсе верно?')
        if data["photofile3"]  == 'Не загружена' and data["photofile2"]  == 'Не загружена' and data["photofile1"]  == 'Не загружена':
            await message.answer(
                f'Ваше имя RU: {data["nameRu"]}\nВаше имя EN: {data["nameEn"]}\nВаш телефон: {data["tel"]}\n'
                f'Ваши инициалы: {data["idn"]}\nВаши контакты: {data["mailcontact"]}\nВаша роль: {data["role"]}'
                f'\nВсе верно?', reply_markup=kb.proverka)

        elif data["photofile3"]  == 'Не загружена' and data["photofile2"]  == 'Не загружена':
            await message.answer_document(data["photofile1"])
            await message.answer(
                f'Ваше имя RU: {data["nameRu"]}\nВаше имя EN: {data["nameEn"]}\nВаш телефон: {data["tel"]}\n'
                f'Ваши инициалы: {data["idn"]}\nВаши контакты: {data["mailcontact"]}\nВаша роль: {data["role"]}\n'
                f'Серийный номер первой камеры: {data["serial1"]}\nВсе верно?', reply_markup=kb.proverka)

        elif data["photofile3"]  == 'Не загружена':
            await message.answer_document(data["photofile1"])
            await message.answer_document(data["photofile2"])
            await message.answer(
                f'Ваше имя RU: {data["nameRu"]}\nВаше имя EN: {data["nameEn"]}\nВаш телефон: {data["tel"]}\n'
                f'Ваши инициалы: {data["idn"]}\nВаши контакты: {data["mailcontact"]}\nВаша роль: {data["role"]}\n'
                f'Серийный номер первой камеры: {data["serial1"]}\nСерийный номер второй камеры: {data["serial2"]}\nВсе верно?', reply_markup=kb.proverka)

        else:
            await message.answer_document(data["photofile1"])
            await message.answer_document(data["photofile2"])
            await message.answer_document(data["photofile3"])
            await message.answer(
                f'Ваше имя RU: {data["nameRu"]}\nВаше имя EN: {data["nameEn"]}\nВаш телефон: {data["tel"]}\n'
                f'Ваши инициалы: {data["idn"]}\nВаши контакты: {data["mailcontact"]}\nВаша роль: {data["role"]}\n'
                f'Серийный номер первой камеры: {data["serial1"]}\nСерийный номер второй камеры: {data["serial2"]}\n'
                f'Серийный номер третьей камеры: {data["serial3"]}\nВсе верно?', reply_markup=kb.proverka)


@router.callback_query(F.data == 'no')
async  def proverka_no(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None)
    await callback.answer('Что Вы хотите изменить?.', show_alert=True)
    data = await state.get_data()
    await callback.message.edit_text(
                f'Ваше имя RU: {data["nameRu"]}\nВаше имя EN: {data["nameEn"]}\nВаш телефон: {data["tel"]}\n'
                f'Ваши инициалы: {data["idn"]}\nВаши контакты: {data["mailcontact"]}\nВаша роль: {data["role"]}\n'
                f'Серийный номер первой камеры: {data["serial1"]}\nСерийный номер второй камеры: {data["serial2"]}\n'
                f'Серийный номер третьей камеры: {data["serial3"]}\nВсе верно?', reply_markup=kb.edit)

#-----------------------------------------------------------------------------------------------------------------------
#   Меню редактирования своих данных
#-----------------------------------------------------------------------------------------------------------------------
@router.callback_query(F.data == 'RU')
async def register_nameRu2(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.set_state(Register.nameRu2)
    await callback_query.message.answer(text='Введите исправления в ваше ФИО на русском языке')

@router.message(Register.nameRu2)
async def register_nameRu2(message: Message, state: FSMContext):
    await state.update_data(nameRu=message.text)
    await state.set_state(Register.verefy)
    await message.answer('Подтвердите изменения',
                         reply_markup=kb.getphoto)

@router.callback_query(F.data == 'EN')
async def register_nameEn2(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.set_state(Register.nameEn2)
    data = await state.get_data()
    await  callback_query.message.answer(text=f'Вы можете внести исправления в ваше имя на английском языке.\n'
                                              f'Сейчас оно такое: {data["nameEn"]}')

@router.message(Register.nameEn2)
async def register_nameEn2(message: Message, state: FSMContext):
    await state.update_data(nameEn=message.text)
    await state.set_state(Register.verefy)
    await message.answer('Подтвердите изменения',
                             reply_markup=kb.getphoto)

@router.callback_query(F.data =='idn')
async  def register_idn2(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.set_state(Register.idn2)
    data = await state.get_data()
    await callback_query.message.answer(text=f'Исправьте ваши инициалы на латинице, они будут подставлены в имя файла ваших фотографий, как пример вот так KNA\n'
                              f'сейчас ваши инициалы такие: Ваши инициалы: {data["idn"]}')
@router.message(Register.idn2)
async  def register_idb2(message: Message, state: FSMContext):
        # Очищаем ввод от всех символов, кроме букв, и приводим к верхнему регистру
        clean_idn = re.sub(r'[^A-Za-z]', '', message.text).upper()
        # Проверяем длину и наличие только букв
        if len(clean_idn) != 3:
            await message.answer(
                "❌ Инициалы должны состоять ровно из трёх латинских букв.\n"
                "Пример: KNA\nПопробуйте ещё раз:"
            )
            return  # Оставляем пользователя в состоянии Register.idn

        # Сохраняем очищенные данные
        await state.update_data(idn=clean_idn)
        await state.set_state(Register.verefy)
        await message.answer('Подтвердите изменения', reply_markup=kb.getphoto)


@router.callback_query(F.data =='contact')
async  def register_mailcontact2(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру по callback_query
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.set_state(Register.mailcontact2)
    data = await state.get_data()
    await callback_query.message.answer(text=f'Исправьте ваши контакты  по которым с вами можно связаться, почта или социальные сети\n'
                              f'сейчас ваши контакты такие: Ваши контакты: {data["mailcontact"]}')

@router.message(Register.mailcontact2)
async  def register_mailcontact2(message: Message, state: FSMContext):
    await state.update_data(mailcontact=message.text)
    await state.set_state(Register.verefy)
    data = await state.get_data()
    await message.answer(text=f'Подтвердите изменения.\n'
                              f'Сейчас ваши контакты такие:  {data["mailcontact"]}', reply_markup=kb.getphoto)

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
    await state.set_state(Register.verefy)
    await callback_query.message.answer('Подтвердите изменения', reply_markup=kb.getphoto)
    await state.clear()

# @router.callback_query(F.data =='phone')
# async  def register_tel2(message: Message, state: FSMContext):




#-----------------------------------------------------------------------------------------------------------------------
#   Конец меню редактирования своих данных
#-----------------------------------------------------------------------------------------------------------------------

@router.callback_query(F.data == 'yes')
async def proverka_yes(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # удаляем инлайн клавиатуру
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None)
    await callback.answer('Вы подтвердили верность данных.', show_alert=True)
    await callback.message.answer('Вы подтвердили верность данных.')
    data = await state.get_data()
    try:
        await rq.set_item(data)
        await callback.message.answer("Данные добавлены в базу данных, спасибо за регистрацию", reply_markup=ReplyKeyboardRemove())
        await fu.number_row(data)
        await state.clear()

    except Exception as e:
            await callback.message.answer(
                f"Ошибка: \n {str(e)}\nОбратитесь к программисту, он денег хочет снова",reply_markup=ReplyKeyboardRemove())
            await state.clear()

# Записываем в БД пользоватлея с его id
#     await rq.set_item(data)
#     await state.clear()
    await state.set_state(StartState.active)


#Выводим данные из базы по запросу
@router.message(F.text == "Можно всех посмотреть")
async def view_all_items(message: types.Message):
    for item in await rq.get_item():
        try:
            await message.answer_document(document=item.serial1,
                                          caption=f'ФИО ru: {item.nameRU}\n'
                                                  f'ФИО en: {item.nameEN}\n'
                                                  f'Инициалы: {item.idn}\n'
                                                  f'Контакты: {item.mailcontact}\n'
                                                  f'Телефон: {item.tel}\n'
                                                  f'Роль: {item.role}',
                                          protect_content=True,
                                          reply_markup=await kb.edit_item(btns={
                                              'Удалить': f'delete_{item.id}',
                                              'Изменить': f'change_{item.id}'})
                                          )
            # запись просто в ячейку
            # sh.wks.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], 'A2')
            # запись просто в последнюю свободную ячейку,но ячейка находится только при старте боета, нужно похоже ассинхронную функцию делать
            # await sh.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], "A{}".format(sh.next_row))
        except TelegramBadRequest:
            await message.answer(text=f'ФИО ru: {item.nameRU}\n'
                                      f'ФИО en: {item.nameEN}\n'
                                      f'Инициалы: {item.idn}\n'
                                      f'Контакты: {item.mailcontact}\n'
                                      f'Телефон: {item.tel}\n'
                                      f'Роль: {item.role}',
                                 protect_content=True,
                                 message_effect_id="5046589136895476101",
                                 reply_markup=await kb.edit_item(btns={
                                     'Удалить': f'delete_{item.id}',
                                     'Изменить': f'change_{item.id}'}))
            # запись просто в ячейку
            # sh.wks.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], 'A2')
            # запись просто в последнюю свободную ячейку,но ячейка находится только при старте боета, нужно похоже ассинхронную функцию делать
            # await fu.number_row(item)
            # await fu.sh.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], "A{}".format(sh.next_row))




    await message.answer("Вот все, любуйся")

#Ловим нажатие на инлайн кнопки по редактированию или удалению
@router.callback_query(F.data.startswith('delete_'))
async def delete_item(callback: CallbackQuery):
    item_id = callback.data.split("_")[-1]
    await  rq.del_item(int(item_id))
    await callback.answer(text=f'Запись удалена')
    await callback.message.answer(text=f'Запись удалена')