import json
import logging

from pathlib import Path
from aiogram import F, Router, types, Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup

from app.Filters.chat_types import ChatTypeFilter, IsAdmin  # импортировали наши личные фильтры
from app.generate import ai_generate
from app.handlers import Gen

from app.Utils.schedule_parser import ScheduleParser
from app.Utils.sheet_writer import SheetWriter

import app.keyboards as kb
import app.database.requests as rq
import app.Sheets.function as fu
import app.Utils.validators as vl


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

# Создаем папку ExportDB для экспорта, если её нет
EXPORT_DIR = Path("ExportDB")
EXPORT_DIR.mkdir(exist_ok=True, parents=True)

@admin_router.message(Command("admin"))
async def admin_keyboard(message: types.Message):
    status = await rq.get_registration_status()
    await message.answer(
        "Панель администратора:",
        reply_markup=await kb.admin_keyboard(status)
    )

# отправляем методом ответа на сообщение стикер по его ID
#     await message.reply_sticker(sticker='CAACAgIAAxkBAAPYZ36b1AUNHQg55cEEfzilVTX1lCYAArkRAAJClVFLVmGP6JmH07A2BA', reply_markup=ReplyKeyboardRemove())
# Получаем ID пользователя и Имя из самого первого сообщения
#    await message.reply(f'Привет :) \nТвой ID: {message.from_user.id}\nИмя: {message.from_user.first_name}\n'
#                        f'Фамилия: {message.from_user.last_name}\nНик: @{message.from_user.username}')
#   await message.reply('Как дела?')


#=======================================================================================================================
# START Получить ID медиа данных
#=======================================================================================================================

# отвечаем на фото его ID
@admin_router.message(F.photo)
async def get_photo(message: Message):
    await message.answer(f'ID фото: {message.photo[-1].file_id}')

# # Отвечаем на документ его ID
# @admin_router.message(F.document)
# async def get_document(message: Message):
#     await message.answer(f'ID документа: {message.document.file_id}')
#
# async def process_document(message: types.Message, bot: Bot):
#     await save_document(message, bot)


# Отвечаем на стикер его ID и ID чата
@admin_router.message(F.sticker)
async def check_sticker(message: Message):
    await message.answer(f'ID стикера: {message.sticker.file_id}')
    await message.answer(f'id чата: {message.from_user.id, message.chat.id}')

#=======================================================================================================================
# END Получить ID медиа данных
#=======================================================================================================================



#Выводим данные из базы по запросу
@admin_router.message(F.text == "Можно всех посмотреть")
async def view_all_items(message: types.Message):
    for item in await rq.get_item():
        try:
            await message.answer_document(document=item.serial1,
                                          caption=f'🪪 ФИО ru: {item.nameRU}\n'
                                                  f'🪪 ФИО en: {item.nameEN}\n'
                                                  f'🪪 Инициалы: {item.idn}\n'
                                                  f'📫 Контакты: {item.mailcontact}\n'
                                                  f'☎️ Телефон: {item.tel}\n'
                                                  f'🪆 Роль: {item.role}',
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
            await message.answer(text=f'🪪 ФИО ru: {item.nameRU}\n'
                                      f'🪪 ФИО en: {item.nameEN}\n'
                                      f'🪪 Инициалы: {item.idn}\n'
                                      f'📫 Контакты: {item.mailcontact}\n'
                                      f'☎️ Телефон: {item.tel}\n'
                                      f'🪆 Роль: {item.role}',
                                 protect_content=True,
                                 message_effect_id="5046589136895476101",
                                 reply_markup=await kb.edit_item(btns={
                                     '🗑️ Удалить': f'delete_{item.id}',
                                     '✏️ Изменить': f'change_{item.id}'}))
            # запись просто в ячейку
            # sh.wks.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], 'A2')
            # запись просто в последнюю свободную ячейку,но ячейка находится только при старте боета, нужно похоже ассинхронную функцию делать
            # await fu.number_row(item)
            # await fu.sh.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], "A{}".format(sh.next_row))

    await message.answer("Вот все, любуйся")

#Ловим нажатие на инлайн кнопки по редактированию или удалению
@admin_router.callback_query(F.data.startswith('delete_'))
async def delete_item(callback: CallbackQuery):
    item_id = callback.data.split("_")[-1]
    await  rq.del_item(int(item_id))
    await callback.answer(text=f'Запись удалена')
    await callback.message.answer(text=f'Запись удалена')



#=======================================================================================================================
# DeepSeek
#=======================================================================================================================
@admin_router.message(F.text == "поговори", )
async def deepseek(message: Message, state: FSMContext):
    await message.answer('Напиши что ты хочешь?')
    await state.set_state(Gen.result)

@admin_router.message(Gen.result)
async def generating(message: Message, state: FSMContext):
    await state.set_state(Gen.wait)
    responses = await ai_generate(message.text)
    await message.answer(responses)
    await state.clear()

@admin_router.message(Gen.wait)
async def stop_flood(message: Message):
    await message.answer('Подожди ты, не так быстро, эй!')
#=======================================================================================================================
# DeepSeek
#=======================================================================================================================



#=======================================================================================================================
# START Открытие или закрытие регистрации
#=======================================================================================================================
@admin_router.callback_query(F.data == 'toggle_registration')
async def toggle_registration(callback: CallbackQuery):
    current_status = await rq.get_registration_status()
    new_status = not current_status
    await rq.set_registration_status(new_status)

    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=await kb.admin_keyboard(new_status)
    )
    await callback.answer(f"Регистрация {'включена' if new_status else 'выключена'}!")
#=======================================================================================================================
# END Открытие или закрытие регистрации
#=======================================================================================================================

#=======================================================================================================================
# START Права на доступ к таблице для менеджера
#=======================================================================================================================
@admin_router.callback_query(F.data == "add_editors_list")
async def show_editors_list(callback: CallbackQuery):
    editors = await rq.get_editors()

    if not editors:
        await callback.message.answer("❌ Нет кандидатов для добавления")
        return

    await callback.message.answer(
        "📋 Список кандидатов в редакторы:",
        reply_markup=await kb.editors_list_keyboard(editors)
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("confirm_editor_"))
async def confirm_editor(callback: CallbackQuery):
    editor_id = int(callback.data.split("_")[-1])
    editor = await rq.get_editor_by_id(editor_id)

    if not editor:
        await callback.message.answer("❌ Пользователь не найден")
        return

    valid_emails = await vl.extract_valid_emails(editor.mailcontact)
    if not valid_emails:
        await callback.message.answer("❌ Нет валидных email в профиле")
        return

    await callback.message.answer(
        f"Добавить пользователя:\n <b>{editor.nameRU}</b>\n"
        f"Email: <code>{valid_emails[0]}</code> в редакторы?",
        parse_mode=ParseMode.HTML,
        reply_markup=await kb.confirmation_keyboard(editor_id, editor.nameRU)
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("add_editor_"))
async def add_editor_final(callback: CallbackQuery):
    editor_id = int(callback.data.split("_")[-1])
    editor = await rq.get_editor_by_id(editor_id)

    if not editor:
        await callback.message.answer("❌ Ошибка: пользователь не найден")
        return

    success = await fu.add_editor_to_sheet(editor.mailcontact)
    if success:
        await callback.message.answer(f"✅ Пользователь {editor.nameRU} добавлен в редакторы!")
    else:
        await callback.message.answer(f"❌ Не удалось добавить {editor.nameRU}")

    await callback.answer()


#======================================================================================================================
# обработчики для импорта/экспорта и загрузки файлов

# Обработчик импорта
@admin_router.callback_query(F.data == 'import_db')
async def import_db_handler(callback: CallbackQuery):
    users = await rq.get_all_users()
    if not users:
        await callback.message.answer("❌ В базе нет пользователей")
        return
    await callback.message.answer(
        "👥 Выберите пользователя:",
        reply_markup=await kb.all_users_keyboard(users)
    )
    await callback.answer()


# Обработчик выгрузки данных пользователя
@admin_router.callback_query(F.data.startswith('export_user_'))
async def export_user_handler(callback: CallbackQuery):
    user_id = int(callback.data.split('_')[-1])
    user = await rq.get_user_by_id(user_id)

    if not user:
        await callback.message.answer("❌ Пользователь не найден")
        return

    # Формируем JSON
    user_data = {
        "id": user.id,
        "name": user.name,
        "nameRU": user.nameRU,
        "nameEN": user.nameEN,
        "idn": user.idn,
        "mailcontact": user.mailcontact,
        "tel": user.tel,
        "role": user.role,
        "serials": [user.serial1, user.serial2, user.serial3],
        "photos": [user.photo1, user.photo2, user.photo3],
        "bild_settings": [
            {
                "os_type": setting.os_type,
                "raw_path": setting.raw_path,
                "folder_format": setting.folder_format
            }
            for setting in user.bild_settings
        ]
    }

    # Сохраняем в папку ExportDB
    filename = EXPORT_DIR / f"db_{user.nameEN}.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)

        # Отправляем файл
        with open(filename, 'rb') as file:
            await callback.message.answer_document(
                document=types.BufferedInputFile(
                    file.read(),
                    filename=f"db_{user.nameEN}.json"
                ),
                caption=f"Данные пользователя:\n1. {user.nameRU}\n"
                        f"2. {user.role}"
            )

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при экспорте: {str(e)}")

    await callback.answer()

# Обработчик экспорта (ожидание файла)
@admin_router.callback_query(F.data == 'export_db')
async def export_db_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📎 Отправьте JSON-файл для импорта в БД")
    await state.set_state("wait_export_file")
    await callback.answer()


# Обработчик принятия файла
@admin_router.message(F.document, StateFilter('wait_export_file'))
async def handle_export_file(message: Message, bot: Bot, state: FSMContext):
    try:
        file = await bot.get_file(message.document.file_id)
        file_data = await bot.download_file(file.file_path)
        user_data = json.loads(file_data.read())

        new_user_data = await rq.create_item_from_data(user_data)
        await message.answer(f"✅ Успешно импортирован: {new_user_data['nameRU']}")

    except ValueError as e:
        await message.answer(f"⚠️ {str(e)}")
    except Exception as e:
        await message.answer(f"❌ Критическая ошибка: {str(e)}")

    await state.clear()

# обработчики для импорта/экспорта и загрузки файлов
#======================================================================================================================

#======================================================================================================================
# Парсинг таблиц

class ScheduleStates(StatesGroup):
    waiting_file = State()
    waiting_project = State()
    waiting_sheet = State()
    confirming_write = State()

# Инициализируем парсер и writer
schedule_parser = ScheduleParser()
sheet_writer = SheetWriter()


@admin_router.callback_query(F.data == "upload_schedule")
async def upload_schedule_callback(callback: CallbackQuery, state: FSMContext):
    """Начало загрузки расписания"""
    await callback.answer()

    # Получаем список доступных листов
    available_sheets = await sheet_writer.get_available_sheets()
    sheets_text = "\n".join(
        [f"• {sheet}" for sheet in available_sheets]) if available_sheets else "• Не удалось загрузить список листов"

    await callback.message.answer(
        "📅 Загрузка расписания в таблицу 'Расписание от Организаторов'\n\n"
        "Отправьте файл с расписанием в формате Excel (.xlsx) или CSV.\n"
        "Файл должен содержать данные для колонок:\n"
        "• Время\n• Место\n• Название\n• Спикеры\n• Описание\n• Трек\n\n"
        f"Доступные листы:\n{sheets_text}"
    )
    await state.set_state(ScheduleStates.waiting_file)


@admin_router.message(ScheduleStates.waiting_file, F.document)
async def handle_schedule_file(message: Message, state: FSMContext, bot: Bot):
    """Обработка файла с расписанием"""
    try:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path

        # Скачиваем файл
        file_data = await bot.download_file(file_path)

        # Парсим файл
        success, parsed_data, message_text = await schedule_parser.parse_file(
            file_data, message.document.file_name
        )

        if not success:
            await message.answer(message_text)
            await state.clear()
            return

        # Сохраняем данные в state
        await state.update_data({
            'parsed_data': parsed_data,
            'filename': message.document.file_name
        })

        # Показываем превью данных
        preview_text = await kb._generate_preview(parsed_data, message_text)
        await message.answer(preview_text)

        # Запрашиваем выбор проекта
        await message.answer(
            "🎯 Выберите проект для записи данных:\n\n"
            "• 🅰️ Проект 1 - запись начиная со строки 31\n"
            "• 🅱️ Проект 2 - запись начиная со строки 112\n\n"
            "Или введите другой номер строки для начала записи:",
            reply_markup=await kb._get_project_selection_keyboard()
        )
        await state.set_state(ScheduleStates.waiting_project)

    except Exception as e:
        logging.error(f"Error handling schedule file: {e}")
        await message.answer(f"❌ Ошибка при обработке файла: {str(e)}")
        await state.clear()


@admin_router.callback_query(ScheduleStates.waiting_project, F.data.in_(["project_1", "project_2", "custom_row"]))
async def handle_project_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора проекта"""
    try:
        if callback.data == "project_1":
            start_row = 31
        elif callback.data == "project_2":
            start_row = 112
        else:  # custom_row
            await callback.message.answer(
                "🔢 Введите номер строки для начала записи данных:"
            )
            await state.set_state(ScheduleStates.waiting_project)
            return

        await state.update_data({'start_row': start_row})

        # Получаем список доступных листов
        available_sheets = await sheet_writer.get_available_sheets()

        if available_sheets:
            await callback.message.answer(
                "📋 Выберите лист для записи данных:",
                reply_markup=await kb._get_sheet_selection_keyboard(available_sheets)
            )
            await state.set_state(ScheduleStates.waiting_sheet)
        else:
            # Используем лист по умолчанию
            await state.update_data({'sheet_name': 'Текущее'})
            await _show_confirmation(callback.message, state)
            await state.set_state(ScheduleStates.confirming_write)

    except Exception as e:
        logging.error(f"Error in handle_project_selection: {e}")
        await callback.message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@admin_router.message(ScheduleStates.waiting_project)
async def handle_custom_row(message: Message, state: FSMContext):
    """Обработка кастомного номера строки"""
    try:
        start_row = int(message.text.strip())

        if start_row < 1:
            await message.answer("❌ Номер строки должен быть положительным числом")
            return

        await state.update_data({'start_row': start_row})

        # Получаем список доступных листов
        available_sheets = await sheet_writer.get_available_sheets()

        if available_sheets:
            await message.answer(
                "📋 Выберите лист для записи данных:",
                reply_markup=await kb._get_sheet_selection_keyboard(available_sheets)
            )
            await state.set_state(ScheduleStates.waiting_sheet)
        else:
            # Используем лист по умолчанию
            await state.update_data({'sheet_name': 'Текущее'})
            await _show_confirmation(message, state)
            await state.set_state(ScheduleStates.confirming_write)

    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный номер строки (целое число)")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@admin_router.callback_query(ScheduleStates.waiting_sheet, F.data.startswith("sheet_"))
async def handle_sheet_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора листа"""
    try:
        sheet_name = callback.data.replace("sheet_", "")
        await state.update_data({'sheet_name': sheet_name})
        await _show_confirmation(callback.message, state)
        await state.set_state(ScheduleStates.confirming_write)

    except Exception as e:
        logging.error(f"Error in handle_sheet_selection: {e}")
        await callback.message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


async def _show_confirmation(message: Message, state: FSMContext):
    """Показывает подтверждение записи"""
    data = await state.get_data()
    parsed_data = data.get('parsed_data', [])
    start_row = data.get('start_row')
    sheet_name = data.get('sheet_name', 'Текущее')

    if not parsed_data or not start_row:
        await message.answer("❌ Ошибка: данные не найдены")
        await state.clear()
        return

    end_row = start_row + len(parsed_data) - 1
    await message.answer(
        f"📝 Подтверждение записи:\n"
        f"• Таблица: Расписание от Организаторов\n"
        f"• Лист: {sheet_name}\n"
        f"• Файл: {data.get('filename', 'N/A')}\n"
        f"• Записей: {len(parsed_data)}\n"
        f"• Диапазон: строки {start_row}-{end_row}\n"
        f"• Колонки: A-F (Время, Место, Название, Спикеры, Описание, Трек)\n\n"
        f"Нажмите '✅ Записать' для подтверждения или '❌ Отменить' для отмены",
        reply_markup=await kb._get_confirmation_keyboard()
    )


@admin_router.callback_query(ScheduleStates.confirming_write, F.data.in_(["confirm_write", "cancel_write"]))
async def handle_confirmation(callback: CallbackQuery, state: FSMContext):
    """Обработка подтверждения записи"""
    try:
        if callback.data == "cancel_write":
            await callback.message.edit_text("❌ Запись отменена")
            await state.clear()
            return

        data = await state.get_data()
        parsed_data = data.get('parsed_data', [])
        start_row = data.get('start_row')
        sheet_name = data.get('sheet_name', 'Текущее')

        if not parsed_data or not start_row:
            await callback.message.edit_text("❌ Ошибка: данные не найдены")
            await state.clear()
            return

        # Записываем данные в таблицу
        await callback.message.edit_text("⏳ Записываю данные в таблицу...")

        success, result_message = await sheet_writer.write_schedule_data(
            parsed_data, start_row, sheet_name
        )

        if success:
            await callback.message.answer(f"✅ {result_message}")

            # Показываем пример записанных данных
            if parsed_data:
                sample_text = "Пример записанных данных:\n"
                for i, event in enumerate(parsed_data[:3]):
                    time = event.get('Время', '')[:20] + "..." if len(event.get('Время', '')) > 20 else event.get(
                        'Время', '')
                    name = event.get('Название', '')[:30] + "..." if len(event.get('Название', '')) > 30 else event.get(
                        'Название', '')
                    sample_text += f"\n{i + 1}. ⏰ {time}\n   📝 {name}"
                await callback.message.answer(sample_text)
        else:
            await callback.message.answer(f"❌ {result_message}")

        await state.clear()

    except Exception as e:
        logging.error(f"Error in handle_confirmation: {e}")
        await callback.message.answer(f"❌ Ошибка при записи данных: {str(e)}")
        await state.clear()

# Парсинг таблиц конец
#======================================================================================================================

