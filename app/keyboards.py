from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

import Texts
# Импортируем определенную функцию, а не все для рабаты функции клавиатуры из БД
from app.database.requests import get_roles
# Импортируем билдер клавиатуры
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
#Импортируем текст для кнопок
from Texts import (Buttons)

import app.database.requests as rq

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
    [InlineKeyboardButton(text=Buttons.GENERAL, callback_data='general')],
    [InlineKeyboardButton(text=Buttons.ALL_TEXTS, callback_data='texts')],
    [InlineKeyboardButton(text=Buttons.ALL, callback_data='all'), InlineKeyboardButton(text=Buttons.DONE, callback_data='ready')],
    [InlineKeyboardButton(text=Buttons.ERROR, callback_data='clear'), InlineKeyboardButton(text=Buttons.NEW, callback_data='new')]
])


table = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Buttons.MAIN, callback_data='main'), InlineKeyboardButton(text=Buttons.DIST, callback_data='путь')]
])


    # ------------------------------------------------------------------------------------------------------------------
    # Клавиатуры админа
    # ------------------------------------------------------------------------------------------------------------------

async def admin_keyboard(registration_enabled: bool) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"Регистрация: {'ON' if registration_enabled else 'OFF'}",
            callback_data='toggle_registration'
        )],
        [InlineKeyboardButton(text="Можно всех посмотреть", callback_data='view_all')],
        [
            InlineKeyboardButton(text="📥 Импорт из БД", callback_data='import_db'),
            InlineKeyboardButton(text="📤 Экспорт в БД", callback_data='export_db')
        ],
        [InlineKeyboardButton(text="DeepSeek", callback_data='deepseek')],
        [InlineKeyboardButton(text="👥 Добавить редакторов", callback_data='add_editors_list')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Клавиатура для админ-подтверждения
async def admin_approval_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"approve_{user_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_{user_id}"
            )
        ]
    ])

async def editors_list_keyboard(editors: list[tuple]) -> InlineKeyboardMarkup:
    """Клавиатура со списком редакторов"""
    builder = InlineKeyboardBuilder()
    for editor_id, name_ru, _ in editors:
        builder.button(
            text=f"👤 {name_ru}",
            callback_data=f"confirm_editor_{editor_id}"
        )
    builder.adjust(1)
    return builder.as_markup()

async def confirmation_keyboard(editor_id: int, name_ru: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения добавления"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ Да, добавить {name_ru}",
        callback_data=f"add_editor_{editor_id}"
    )
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    builder.adjust(1)
    return builder.as_markup()

# Новая функция для клавиатуры со всеми пользователями
async def all_users_keyboard(users: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        builder.button(
            text=f"{user.nameRU}",
            callback_data=f"export_user_{user.id}"
        )
    builder.adjust(1)
    return builder.as_markup()

    # ------------------------------------------------------------------------------------------------------------------
    # Клавиатуры админа
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # Клавиатуры билда
    # ------------------------------------------------------------------------------------------------------------------

async def os_select_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Windows 🖥️", callback_data="windows"),
        InlineKeyboardButton(text="MacOS 🍏", callback_data="macos"),
        width=2
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_setup"),
        width=1
    )
    return builder.as_markup()

async def folder_format_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1: Число_Месяц/Название_Съёмки", callback_data="format_1"),
        InlineKeyboardButton(text="2: Число_Месяц/Время Название_Съёмки", callback_data="format_2"),
        InlineKeyboardButton(text="3: Месяц/Число/Название_Съёмки", callback_data="format_3"),
        width=1
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_setup"),
        width=1
    )
    return builder.as_markup()

async def settings_confirmation_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Оставить как есть", callback_data="keep_settings"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data="change_settings")
            ]
        ]
    )

    # ------------------------------------------------------------------------------------------------------------------
    # Клавиатуры билда
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # Клавиатуры Помощь
    # ------------------------------------------------------------------------------------------------------------------
help = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=Texts.Buttons.PHOTO, callback_data='Photo')],
    [InlineKeyboardButton(text='Изменить ваше имя EN', callback_data='EN')],
    [InlineKeyboardButton(text='Изменить ваш телефон', callback_data='phone')],
    [InlineKeyboardButton(text='Изменить ваши инициалы', callback_data='idn')],
    [InlineKeyboardButton(text='Изменить ваши контакты', callback_data='contact')],
    [InlineKeyboardButton(text='Изменить вашу роль', callback_data='role')],
    [InlineKeyboardButton(text='Оставить так и подтвердить', callback_data='yes')]])


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
        keyboard.add(InlineKeyboardButton(text=role.name, callback_data=f"role_{role.id}"))
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


# async def create_task_keyboard(row: int, col: int, code: str) -> InlineKeyboardMarkup:
#     """
#     Создаёт клавиатуру для задачи с динамическими параметрами
#     :param row: Номер строки в таблице
#     :param col: Номер колонки в таблице
#     """
#     builder = InlineKeyboardBuilder()
#     builder.button(text=Buttons.DONE, callback_data=f"done:{row}:{col}")
#     builder.button(text=Buttons.CANCEL, callback_data=f"cancel:{row}:{col}")
#     builder.button(text=Buttons.CODE.format(code), callback_data=f"code:{row}:{col}")
#     builder.button(text=Buttons.ERROR, callback_data=f"error:{row}:{col}")
#
#     # Настройка расположения кнопок: первые две кнопки в одной строке, третья — в другой
#     builder.adjust(2, 1, 1)
#     return builder.as_markup()

# Новая клавиатура для редактирования сообщений после изменения статуса съемки.
async def create_task_keyboard(row: int, col: int, code: str, message_id: int) -> InlineKeyboardMarkup:
    """Добавляем message_id в callback data"""
    builder = InlineKeyboardBuilder()
    # builder.button(text=Buttons., callback_data=f"done:{row}:{col}:{message_id}")
    builder.button(text=Buttons.DONE, callback_data=f"done:{row}:{col}:{code}:{message_id}")
    builder.button(text=Buttons.CODE.format(code), callback_data=f"code:{row}:{col}:{code}:{message_id}")
    builder.button(text=Buttons.CANCEL, callback_data=f"cancel:{row}:{col}:{code}:{message_id}")
    builder.button(text=Buttons.ERROR, callback_data=f"error:{row}:{col}:{code}:{message_id}")
    builder.adjust(1, 1, 2)
    return builder.as_markup()

async def status_done_error(row: int, col: int, code: str, message_id: int) -> InlineKeyboardMarkup:
    """Добавляем message_id в callback data"""
    builder = InlineKeyboardBuilder()
    builder.button(text=Buttons.DONE, callback_data=f"done:{row}:{col}:{code}:{message_id}")
    builder.button(text=Buttons.ERROR, callback_data=f"error:{row}:{col}:{code}:{message_id}")
    builder.adjust( 1, 1)
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


async def create_inline_keyboard(
        *btns: str,
        callback_data: dict[int, str] = None,
        url: dict[int, str] = None,
        sizes: tuple[int, ...] = (2,),
):
    """
    Создает инлайн-клавиатуру с кнопками.

    Параметры:
        *btns: тексты кнопок
        callback_data: словарь {индекс кнопки: callback_data}
        url: словарь {индекс кнопки: URL}
        sizes: размеры рядов (по умолчанию (2,))

    Пример использования:
    create_inline_keyboard(
        "Меню",
        "О магазине",
        "Варианты оплаты",
        "Варианты доставки",
        "Наш сайт",
        callback_data={0: "menu", 1: "about", 2: "payment", 3: "delivery"},
        url={4: "https://example.com"},
        sizes=(2, 2, 1)
    )
    """
    keyboard = InlineKeyboardBuilder()
    callback_data = callback_data or {}
    url = url or {}

    for index, text in enumerate(btns):
        if index in callback_data:
            keyboard.button(text=text, callback_data=callback_data[index])
        elif index in url:
            keyboard.button(text=text, url=url[index])
        else:
            # Используем текст кнопки как callback_data по умолчанию
            keyboard.button(text=text, callback_data=text)

    keyboard.adjust(*sizes)
    return keyboard.as_markup()

# # функция для клавиатур в зависимости от роли
# async def get_role_keyboard(role: str) -> ReplyKeyboardMarkup:
#     if role == "Фотограф":
#         return ReplyKeyboardMarkup(
#             keyboard=[
#                 [KeyboardButton(text="расписание")],
#                 [KeyboardButton(text="🔄 Редактировать данные")],
#                 [KeyboardButton(text="📋 Мои серийники")]
#             ],
#             resize_keyboard=True
#         )
#     elif role == "Билд-редактор":
#         return ReplyKeyboardMarkup(
#             keyboard=[
#                 [KeyboardButton(text="📊 Таблицы")],
#                 [KeyboardButton(text="🔍 Поиск кода")],
#                 [KeyboardButton(text="📂 Все фотографы")]
#             ],
#             resize_keyboard=True
#         )
#     return main  # Стандартная клавиатура

# функция для клавиатур в зависимости от роли
async def get_role_keyboard(role: str) -> InlineKeyboardMarkup:
    if role == "Фотограф":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📸 Моё расписание", callback_data="schedule_pers")],
                [InlineKeyboardButton(text="🔄 Редактировать данные", callback_data="edit_data")],
                [InlineKeyboardButton(text="📋 Мои серийники", callback_data="my_serials")]
            ]
        )
    elif role == "Билд-редактор":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 Таблица Day", callback_data="tables_day"), InlineKeyboardButton(text="📊 Таблица путь", callback_data="tables_dist")],
                [InlineKeyboardButton(text="📊 Таблица Расписание Фото", callback_data="tables_shedule")],
                [InlineKeyboardButton(text="Подготовить PhotoMechanic", callback_data="PM_data")],
                [InlineKeyboardButton(text="🔍 Поиск кода", callback_data="search_code")],
                [InlineKeyboardButton(text="📂 Все фотографы", callback_data="all_photographers")]
            ]
        )
    elif role == "Менеджер":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 Таблица Фото", callback_data="tables_photo"), InlineKeyboardButton(text="📊 Таблица Расписание", callback_data="tables_shedule")],
                [InlineKeyboardButton(text="🔍 Поиск кода", callback_data="search_code")],
                [InlineKeyboardButton(text="📂 Все фотографы", callback_data="all_photographers")]
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=[])  # Возвращаем пустую клавиатуру или основную, если есть

# функция создания кнопок с именами фотографов
async def photographers_keyboard():
    photographers = await rq.get_all_photographers()
    builder = InlineKeyboardBuilder()

    for idn, nameRU in photographers:
        builder.button(
            text=nameRU,
            callback_data=f"photographer_{idn}"
        )

    builder.adjust(1)
    return builder.as_markup()