from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardMarkup, \
    InlineKeyboardButton, Update
# Импортируем определенную функцию, а не все для рабаты функции клавиатуры из БД
from app.database.requests import get_roles
# Импортируем билдер клавиатуры
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
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

fio = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Buttons.RU, callback_data='ru')],
    [InlineKeyboardButton(text=Buttons.EN, callback_data='en')],
    [InlineKeyboardButton(text=Buttons.CHECK, callback_data='check')]])

get_tel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=Buttons.PHONE,
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
    [InlineKeyboardButton(text='Оставить так и подтвердить', callback_data='yes')]])

cancel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Buttons.YES, callback_data='yes')],
    [InlineKeyboardButton(text=Buttons.NO, callback_data='no')]])

find = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Buttons.ALL, callback_data='all'), InlineKeyboardButton(text=Buttons.DONE, callback_data='ready')],
    [InlineKeyboardButton(text=Buttons.ERROR, callback_data='clear'), InlineKeyboardButton(text=Buttons.NEW, callback_data='new')]
])


table = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Buttons.MAIN, callback_data='main'), InlineKeyboardButton(text=Buttons.DIST, callback_data='путь')]
])


    # ------------------------------------------------------------------------------------------------------------------
    # Клавиатуры админа
    # ------------------------------------------------------------------------------------------------------------------

admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Buttons.ALL, callback_data='all'), InlineKeyboardButton(text=Buttons.DONE, callback_data='ready')],
    [InlineKeyboardButton(text=Buttons.ERROR, callback_data='clear'), InlineKeyboardButton(text=Buttons.NEW, callback_data='new')]
])






    # ------------------------------------------------------------------------------------------------------------------
    # Клавиатуры админа
    # ------------------------------------------------------------------------------------------------------------------



    # ------------------------------------------------------------------------------------------------------------------
    # Клавиатуры, которые генерируются функциями
    # ------------------------------------------------------------------------------------------------------------------


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


# Кнопка как функции, в которую передаётся словарь и возвращаемые значения из места где её вызывают
async def edit_item(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,)):

        keydoard = InlineKeyboardBuilder()

        for text, data in btns.items():
            keydoard.add(InlineKeyboardButton(text=text, callback_data=data))
        return keydoard.adjust(*sizes).as_markup()


async def create_task_keyboard(row: int, col: int, code: str) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру для задачи с динамическими параметрами
    :param row: Номер строки в таблице
    :param col: Номер колонки в таблице
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=Buttons.DONE, callback_data=f"done:{row}:{col}")
    builder.button(text=Buttons.CANCEL, callback_data=f"cancel:{row}:{col}")
    builder.button(text=Buttons.CODE.format(code), callback_data=f"code:{row}:{col}")
    builder.button(text=Buttons.ERROR, callback_data=f"error:{row}:{col}")

    # Настройка расположения кнопок: первые две кнопки в одной строке, третья — в другой
    builder.adjust(2, 1, 1)
    return builder.as_markup()

# edit_item = InlineKeyboardMarkup(inline_keyboard=[
#     [InlineKeyboardButton(text='Удалить', callback_data='del')],
#     [InlineKeyboardButton(text='Изменить', callback_data='edit')]])

# Создать функцию, которая будет удалять инлайн кнопки в ответе бота:

async def create_keyboard(
    *btns: str,
    placeholder: str = None,
    request_contact: int = None,
    request_location: int = None,
    sizes: tuple[int] = (2,),
):
    '''
    Parameters request_contact and request_location must be as indexes of btns args for buttons you need.
    Example:
    get_keyboard(
            "Меню",
            "О магазине",
            "Варианты оплаты",
            "Варианты доставки",
            "Отправить номер телефона"
            placeholder="Что вас интересует?",
            request_contact=4,
            sizes=(2, 2, 1)
        )
    '''
    keyboard = ReplyKeyboardBuilder()

    for index, text in enumerate(btns, start=0):

        if request_contact and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))

        elif request_location and request_location == index:
            keyboard.add(KeyboardButton(text=text, request_location=True))
        else:

            keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(
            resize_keyboard=True, input_field_placeholder=placeholder)