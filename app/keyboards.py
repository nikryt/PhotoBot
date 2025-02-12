from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardMarkup, \
    InlineKeyboardButton, Update
# Импортируем определенную функцию, а не все для рабаты функции клавиатуры из БД
from app.database.requests import get_roles
# Импортируем билдер клавиатуры
from aiogram.utils.keyboard import InlineKeyboardBuilder
#Импортируем текст для кнопок
from Texts import (Buttons)

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=Buttons.FIO)],
    [KeyboardButton(text=Buttons.CONTACTS)],
    [KeyboardButton(text=Buttons.PHOTO),
    KeyboardButton(text=Buttons.CHECK)]],
    resize_keyboard=True,
    input_field_placeholder='Выберите куда вернутся...')

getphoto = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=Buttons.FINISH_UPLOAD,)]],
                            resize_keyboard=True)

back_cancel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Buttons.BACK, callback_data='back'),
    InlineKeyboardButton(text=Buttons.CANCEL, callback_data='cancel')]
])

# Создаем клавиатуру с роями из базы данных
async def roles():
    all_roles = await get_roles()
    keyboard = InlineKeyboardBuilder()
# Достали все роли и итерируем их
    for role in all_roles:
#       Передача в callback_data roles_1-2-3-4...
#       keyboard.add(InlineKeyboardButton(text=role.name, callback_data=f"roles_{role.id}"))
        keyboard.add(InlineKeyboardButton(text=role.name, callback_data=role.name))
        # print(InlineKeyboardButton(text=role.name, callback_data=role.name))
    return keyboard.adjust(2).as_markup()

fio = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='На русском', callback_data='ru')],
    [InlineKeyboardButton(text='На  английском', callback_data='en')],
    [InlineKeyboardButton(text=Buttons.CHECK, callback_data='check')]])

get_tel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='📱 Отправить номер',
                    request_contact=True)]],
                    resize_keyboard=True, one_time_keyboard=True)

proverka = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Buttons.YES, callback_data='yes')],
    [InlineKeyboardButton(text=Buttons.NO, callback_data='no')]])

edit = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Изменить ваше имя RU', callback_data='RU')],
    [InlineKeyboardButton(text='Изменить ваше имя EN', callback_data='EN')],
    [InlineKeyboardButton(text='Изменить ваш телефон', callback_data='phone')],
    [InlineKeyboardButton(text='Изменить ваши инициалы', callback_data='idn')],
    [InlineKeyboardButton(text='Изменить ваши контакты', callback_data='contact')],
    [InlineKeyboardButton(text='Изменить вашу роль', callback_data='role')],
    [InlineKeyboardButton(text='Оставить так', callback_data='yes')]])

cancel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Buttons.YES, callback_data='yes')],
    [InlineKeyboardButton(text=Buttons.NO, callback_data='no')]])

# Кнопка как функуия в которую передаётся словарь и возвращаемые значения из места где её вызывают
async def edit_item(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,)):

        keydoard = InlineKeyboardBuilder()

        for text, data in btns.items():
            keydoard.add(InlineKeyboardButton(text=text, callback_data=data))
        return keydoard.adjust(*sizes).as_markup()

# edit_item = InlineKeyboardMarkup(inline_keyboard=[
#     [InlineKeyboardButton(text='Удалить', callback_data='del')],
#     [InlineKeyboardButton(text='Изменить', callback_data='edit')]])

# Создать функцию, которая будет удалять инлайн кнопки в ответе бота:
