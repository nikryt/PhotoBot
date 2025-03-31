import asyncio
import logging
import os
import re
from pathlib import Path

from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import Texts
import app.database.requests as rq
import app.Sheets.function as fu
import app.keyboards as kb
import app.Utils.XMP_edit as pm
import app.Utils.validators as vl

from aiogram import Router, F, types
from aiogram.types import CallbackQuery, FSInputFile
from dotenv import load_dotenv


from Texts import Messages


bild_router = Router()


# Класс состояний FSM
class BildStates(StatesGroup):
    os_type = State()
    raw_path = State()
    folder_format = State()
    confirm_settings = State()


# Начало процесса настройки
@bild_router.message(F.text == '/setup')
async def start_setup(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверяем существующие настройки
    item = await rq.get_item_by_tg_id(user_id)
    if item and item.bild_settings:
        # Получаем последние настройки
        latest_settings = item.bild_settings[-1]

        # Формируем сообщение с текущими настройками
        settings_text = (
            "⚙️ Текущие настройки:\n"
            f"• ОС: {latest_settings.os_type}\n"
            f"• Путь: {latest_settings.raw_path}\n"
            f"• Формат: {latest_settings.folder_format}\n\n"
            "Хотите изменить их или оставить как есть?"
        )

        await message.answer(
            settings_text,
            reply_markup=await kb.settings_confirmation_keyboard()  # Новая клавиатура
        )
        await state.set_state(BildStates.confirm_settings)
    else:
        # Стандартный процесс настройки
        await message.answer(
            Messages.BILD_PM,
            parse_mode=ParseMode.HTML,
            reply_markup=await kb.os_select_keyboard()
        )
        await state.set_state(BildStates.os_type)


# Обработчик подтверждения настроек
@bild_router.callback_query(BildStates.confirm_settings, F.data.in_(['keep_settings', 'change_settings']))
async def process_settings_confirmation(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'keep_settings':
        await callback.message.edit_text("✅ Настройки сохранены!")
        await state.clear()
    else:
        # Запускаем процесс изменения настроек
        await callback.message.edit_text(
            Messages.BILD_PM,
            parse_mode=ParseMode.HTML,
            reply_markup=await kb.os_select_keyboard()
        )
        await state.set_state(BildStates.os_type)

    await callback.answer()

@bild_router.callback_query(BildStates.os_type, F.data.in_(['windows', 'macos']))
async def process_os_select(callback: CallbackQuery, state: FSMContext):
    os_type = callback.data
    await state.update_data(os_type=os_type)

    # Выбираем текст в зависимости от ОС
    if os_type == 'windows':
        text = Texts.Messages.BILD_STORAGE_WIN
    else:
        text = Texts.Messages.BILD_STORAGE_MAC

    await callback.message.edit_text(text, parse_mode=ParseMode.HTML)
    await state.set_state(BildStates.raw_path)


# Обработка ввода пути
@bild_router.message(BildStates.raw_path)
async def process_raw_path(message: types.Message, state: FSMContext):
    user_path = message.text.strip()
    data = await state.get_data()
    os_type = data.get('os_type', 'windows')

    # Минимальная проверка длины
    if len(user_path) < 3:
        return await message.answer(Texts.Messages.BILD_STORAGE_ERR, parse_mode=ParseMode.HTML)

    # Валидация пути
    is_valid, error_msg = False, ""

    if os_type == 'windows':
        is_valid, error_msg = await vl.validate_windows_path(user_path)
    elif os_type in ('macos'):
        is_valid, error_msg = await vl.validate_unix_path(user_path, os_type)

    if not is_valid:
        return await message.answer(error_msg, parse_mode=ParseMode.HTML)

    # Нормализация пути
    try:
        normalized_path = await vl.normalize_path(user_path, os_type)
    except ValueError as e:
        return await message.answer(f"❌ {str(e)}", parse_mode=ParseMode.HTML)

    # Сохраняем и переходим к следующему шагу
    await state.update_data(raw_path=normalized_path)
    await message.answer(
        Texts.Messages.BILD_MANUAL,
        parse_mode=ParseMode.HTML,
        reply_markup=await kb.folder_format_keyboard()
    )
    await state.set_state(BildStates.folder_format)


# Обработка выбора формата папки
# @bild_router.callback_query(BildStates.folder_format, F.data.in_(['format_1', 'format_2', 'format_3']))
# async def process_folder_format(callback: CallbackQuery, state: FSMContext):
#     data = await state.get_data()
#     user_id = callback.from_user.id
#
#     # Получаем последний item пользователя
#     item = await rq.get_item_by_tg_id(user_id)
#     if not item:
#         await callback.message.edit_text("❌ Ошибка: запись пользователя не найдена")
#         await callback.answer()
#         return
#     logging.info(item)
#
#     # Получаем значение формата из Google Sheets
#     format_value = await fu.get_genm_format(callback.data)
#     if not format_value:
#         await callback.message.edit_text("❌ Ошибка: шаблон не найден")
#         await callback.answer()
#         return
#     logging.info(format_value)
#
#     # Сохранение данных
#     await rq.save_bild_settings(
#         item_id=item.id,
#         os_type=data['os_type'],
#         raw_path=data['raw_path'],
#         folder_format=format_value
#     )
#
#     await callback.message.edit_text("✅ Настройки успешно сохранены!")
#     await callback.answer()


@bild_router.callback_query(BildStates.folder_format, F.data.in_(['format_1', 'format_2', 'format_3']))
async def process_folder_format(callback: CallbackQuery, state: FSMContext):
    try:
        # Уведомление о начале обработки
        await callback.message.edit_text("⏳ Ваши данные обрабатываются...")
        await callback.answer()

        data = await state.get_data()
        user_id = callback.from_user.id

        # Получаем запись пользователя с настройками
        item = await rq.get_item_by_tg_id(user_id)
        if not item:
            await callback.message.edit_text("❌ Ошибка: запись пользователя не найдена")
            return

        # Получаем формат из Google Sheets
        format_value = await fu.get_genm_format(callback.data)
        if not format_value:
            await callback.message.edit_text("❌ Ошибка: шаблон не найден")
            return

        # Проверяем существующие настройки через item.bild_settings
        existing_settings = item.bild_settings[-1] if item.bild_settings else None

        if existing_settings:
            # Обновляем существующую запись
            await rq.update_bild_settings(
                settings_id=existing_settings.id,
                os_type=data['os_type'],
                raw_path=data['raw_path'],
                folder_format=format_value
            )
            success_msg = "✅ Настройки успешно обновлены!"
        else:
            # Создаем новую запись
            await rq.save_bild_settings(
                item_id=item.id,
                os_type=data['os_type'],
                raw_path=data['raw_path'],
                folder_format=format_value
            )
            success_msg = "✅ Настройки успешно сохранены!"

        # Обновляем сообщение
        await callback.message.edit_text(success_msg)
        await state.clear()

    except IndexError:
        logging.error("Список bild_settings пуст или некорректен")
        await callback.message.edit_text("❌ Ошибка: повреждены данные настроек")
    except Exception as e:
        logging.error(f"Ошибка сохранения: {str(e)}", exc_info=True)
        await callback.message.edit_text("❌ Критическая ошибка при сохранении")

# Отмена настройки
@bild_router.callback_query(F.data == 'cancel_setup')
async def cancel_setup(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Настройка отменена")
    await callback.answer()



# @bild_router.callback_query(F.data == 'PM_data')
# async def handle_pm_data_request(callback: types.CallbackQuery):
#     """
#     Обработчик запроса на генерацию XMP файла
#     """
#     try:
#         user_id = callback.from_user.id
#
#         # Получаем данные пользователя
#         if not (user_data := await rq.get_user_data(user_id)):
#             await callback.answer("❌ Ваши данные не найдены", show_alert=True)
#             return
#
#         # Проверяем обязательные поля
#         if not all([user_data.get('idn'), user_data.get('mailcontact')]):
#             await callback.answer("❌ Отсутствуют необходимые данные (инициалы или контакты)", show_alert=True)
#             return
#
#         # Пути к файлам
#         base_dir = Path('app') / 'PhotoMechanic'
#         source_file = base_dir / 'PM_Metadata.XMP'
#
#         # Обработка XMP
#         if not (output_file := process_single_xmp(
#                 initials=user_data['idn'],
#                 contacts=user_data['mailcontact'],
#                 input_file=source_file
#         )):
#             raise RuntimeError("Не удалось обработать XMP файл")
#
#         # Отправка файла пользователю
#         await callback.message.answer_document(
#             FSInputFile(output_file),
#             caption="✅ Ваш XMP файл готов"
#         )
#         await callback.answer()
#
#     except Exception as e:
#         logging.error(f"Ошибка обработки запроса PM_data от {user_id}: {e}")
#         await callback.answer("❌ Произошла ошибка при генерации файла", show_alert=True)

# @bild_router.callback_query(F.data == 'PM_data')
# async def handle_pm_data_request(callback: types.CallbackQuery):
#     """
#     Обработчик запроса на генерацию XMP и SNAP файлов
#     """
#     try:
#         user_id = callback.from_user.id
#
#         # Получаем данные пользователя
#         if not (user_data := await rq.get_user_data(user_id)):
#             await callback.answer(Texts.Messages.PM_BILD_DATA_NOFIND, show_alert=True)
#             return
#
#         # Проверяем обязательные поля
#         required_fields = ['idn', 'mailcontact']
#         if not all(user_data.get(field) for field in required_fields):
#             await callback.answer(Texts.Messages.PM_BILD_DATA_ERR, show_alert=True)
#             return
#
#         # Фильтруем почтовые адреса из контактов
#         # Фильтрация контактов
#         contacts = await vl.filter_emails(user_data['mailcontact'])
#         if contacts is None:
#             contacts = "Контактная информация"
#             logging.warning(f"No valid contacts after filtering for user {user_id}")
#
#         # Пути к файлам
#         base_dir = Path('app') / 'PhotoMechanic'
#         source_file = base_dir / 'PM_Metadata.XMP'
#
#         # Асинхронно обрабатываем XMP
#         try:
#             output_xmp = await asyncio.to_thread(
#                 pm.process_single_xmp,
#                 initials=user_data['idn'],
#                 contacts=contacts,  # Используем отфильтрованные контакты
#                 input_file=source_file
#             )
#             if not output_xmp:
#                 raise RuntimeError("XMP processing failed")
#         except Exception as e:
#             logging.error(f"XMP error: {e}")
#             await callback.answer("❌ Ошибка при создании XMP", show_alert=True)
#             return
#
#         # Асинхронно создаем SNAP
#         try:
#             output_snap = await asyncio.to_thread(
#                 pm.create_snap_file,
#                 initials=user_data['idn'],
#                 input_xmp=output_xmp
#             )
#             if not output_snap:
#                 raise RuntimeError("SNAP creation failed")
#         except Exception as e:
#             logging.error(f"SNAP error: {e}")
#             await callback.answer("❌ Ошибка при создании SNAP", show_alert=True)
#             return
#
#         # Отправка SNAP файла
#         await callback.message.answer_document(
#             FSInputFile(output_snap),
#             caption=Texts.Caption.SNAP_IPTC
#         )
#
#         # Опционально: отправка XMP файла
#         await callback.message.answer_document(
#             FSInputFile(output_xmp),
#             caption=Texts.Caption.XMP_IPTC
#         )
#
#         await callback.answer()
#
#     except Exception as e:
#         logging.error(f"Global error: {e}")
#         await callback.answer("❌ Критическая ошибка при обработке", show_alert=True)

@bild_router.callback_query(F.data == 'PM_data')
async def handle_pm_data_request(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик создания Ingest.snap с данными из БД"""
    try:
        user_id = callback.from_user.id

        # Получаем данные пользователя из БД
        user_data = await rq.get_user_data(user_id)
        if not user_data or not all(user_data.get(f) for f in ['idn', 'mailcontact']):
            await callback.answer("❌ Данные пользователя не найдены", show_alert=True)
            return

        # Получаем item с загруженными настройками
        item = await rq.get_item_by_tg_id(user_id)
        if not item or not item.bild_settings:
            await callback.answer("❌ Настройки не найдены", show_alert=True)
            return

        # Берем последнюю настройку
        latest_settings = item.bild_settings[-1]

        # Получаем настройки из БД
        bild_settings = await rq.get_bild_settings(item.id)
        if not bild_settings:
            await callback.answer("❌ Настройки не найдены", show_alert=True)
            return

        # Проверяем наличие os_type
        os_type = getattr(bild_settings, 'os_type', '').lower()
        if not os_type:
            await callback.answer("❌ Тип ОС не указан в настройках", show_alert=True)
            return

        # Определяем подписи в зависимости от OS
        captions = {
            'windows': {
                'ingest': Texts.Caption.INGEST_SNAP_WIN,
                'snap': Texts.Caption.SNAP_IPTC_WIN,
                'xmp': Texts.Caption.XMP_IPTC_WIN,
                'name': Texts.Caption.RENAME_SNAP_WIN
            },
            'macos': {
                'ingest': Texts.Caption.INGEST_SNAP_MAC,
                'snap': Texts.Caption.SNAP_IPTC_MAC,
                'xmp': Texts.Caption.XMP_IPTC_MAC,
                'name': Texts.Caption.RENAME_SNAP_MAC
            }
        }

        default_captions = {
            'ingest': "⚙️ Ingest файл с настройками",
            'snap': Texts.Caption.SNAP_IPTC_WIN,
            'xmp': Texts.Caption.XMP_IPTC_WIN,
            'name': Texts.Caption.RENAME_SNAP_WIN
        }

        # Выбираем подходящие подписи
        selected_captions = captions.get(os_type, default_captions)

        # Фильтрация контактов
        contacts = await vl.filter_emails(user_data['mailcontact']) or "Контактная информация"

        # Пути к файлам
        base_dir = Path('app') / 'PhotoMechanic'
        source_xmp = base_dir / 'PM_Metadata.XMP'
        source_ingest = base_dir / 'Ingest.snap'
        source_rename = base_dir / 'Rename.snap'

        # Проверка существования исходных файлов
        required_files = [source_xmp, source_ingest, source_rename]
        for file in required_files:
            if not file.exists():
                logging.error(f"Файл {file.name} не найден: {file}")
                await callback.answer(f"❌ Файл {file.name} отсутствует", show_alert=True)
                return

        # Обработка файлов
        output_xmp = await asyncio.to_thread(
            pm.process_single_xmp,
            user_data['idn'],
            contacts,
            source_xmp
        )
        if not output_xmp or not output_xmp.exists():
            await callback.answer("❌ Ошибка создания XMP", show_alert=True)
            return

        output_snap = await asyncio.to_thread(
            pm.create_snap_file,
            user_data['idn'],
            output_xmp
        )
        if not output_snap or not output_snap.exists():
            await callback.answer("❌ Ошибка создания SNAP", show_alert=True)
            return

        # Чтение SNAP-контента
        try:
            with open(output_snap, 'r', encoding='utf-8') as f:
                snap_content = f.read()
        except Exception as e:
            logging.error(f"Ошибка чтения SNAP: {e}")
            await callback.answer("❌ Ошибка чтения файла", show_alert=True)
            return

        # Создание модифицированного Ingest
        output_ingest = await asyncio.to_thread(
            pm.create_ingest_snap,
            initials=user_data['idn'],
            raw_path=latest_settings.raw_path,
            folder_format=bild_settings.folder_format,
            input_ingest=source_ingest,
            snap_content=snap_content
        )
        if not output_ingest or not output_ingest.exists():
            await callback.answer("❌ Ошибка создания Ingest", show_alert=True)
            return

        # Формируем список файлов с подписями
        files = [
            (output_ingest, selected_captions['ingest']),
            (output_snap, selected_captions['snap']),
            (source_rename, selected_captions['name']),
            (output_xmp, selected_captions['xmp']),
        ]

        # Отправка файлов
        for file, caption in files:
            if file.exists():
                await callback.message.answer_document(FSInputFile(file), caption=caption, parse_mode=ParseMode.HTML)
            else:
                logging.warning(f"Файл {file.name} не найден, пропуск отправки")

        await callback.answer()
        await state.clear()

    except Exception as e:
        logging.error(f"Ошибка обработки PM_data: {str(e)}")
        await callback.answer("❌ Критическая ошибка при генерации", show_alert=True)