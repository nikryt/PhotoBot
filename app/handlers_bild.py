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


# Начало процесса настройки
@bild_router.message(F.text == '/setup')
async def start_setup(message: types.Message, state: FSMContext):
    await message.answer(
        Messages.BILD_PM,
        parse_mode=ParseMode.HTML,
        reply_markup=await kb.os_select_keyboard()
    )
    await state.set_state(BildStates.os_type)


# Обработка выбора ОС
@bild_router.callback_query(BildStates.os_type, F.data.in_(['windows', 'macos']))
async def process_os_select(callback: CallbackQuery, state: FSMContext):
    await state.update_data(os_type=callback.data)
    await callback.message.edit_text(Texts.Messages.BILD_STORAGE, parse_mode=ParseMode.HTML)
    await state.set_state(BildStates.raw_path)


# Обработка ввода пути
@bild_router.message(BildStates.raw_path)
async def process_raw_path(message: types.Message, state: FSMContext):
    if len(message.text) < 3:  # Минимальная проверка пути
        return await message.answer(Texts.Messages.BILD_STORAGE_ERR, parse_mode = ParseMode.HTML)

    await state.update_data(raw_path=message.text)
    await message.answer(
        Texts.Messages.BILD_MANUAL,
        parse_mode=ParseMode.HTML,
        reply_markup=await kb.folder_format_keyboard()
    )
    await state.set_state(BildStates.folder_format)


# Обработка выбора формата папки
@bild_router.callback_query(BildStates.folder_format, F.data.in_(['format1', 'format2', 'format3']))
async def process_folder_format(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    # Сохранение данных в БД
    await rq.save_bild_settings(
        user_id=callback.from_user.id,
        os_type=data['os_type'],
        raw_path=data['raw_path'],
        folder_format=callback.data
    )

    await callback.message.edit_text("✅ Настройки успешно сохранены!")
    await callback.answer()


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

@bild_router.callback_query(F.data == 'PM_data')
async def handle_pm_data_request(callback: types.CallbackQuery):
    """
    Обработчик запроса на генерацию XMP и SNAP файлов
    """
    try:
        user_id = callback.from_user.id

        # Получаем данные пользователя
        if not (user_data := await rq.get_user_data(user_id)):
            await callback.answer(Texts.Messages.PM_BILD_DATA_NOFIND, show_alert=True)
            return

        # Проверяем обязательные поля
        required_fields = ['idn', 'mailcontact']
        if not all(user_data.get(field) for field in required_fields):
            await callback.answer(Texts.Messages.PM_BILD_DATA_ERR, show_alert=True)
            return

        # Фильтруем почтовые адреса из контактов
        # Фильтрация контактов
        contacts = await vl.filter_emails(user_data['mailcontact'])
        if contacts is None:
            contacts = "Контактная информация"
            logging.warning(f"No valid contacts after filtering for user {user_id}")

        # Пути к файлам
        base_dir = Path('app') / 'PhotoMechanic'
        source_file = base_dir / 'PM_Metadata.XMP'

        # Асинхронно обрабатываем XMP
        try:
            output_xmp = await asyncio.to_thread(
                pm.process_single_xmp,
                initials=user_data['idn'],
                contacts=contacts,  # Используем отфильтрованные контакты
                input_file=source_file
            )
            if not output_xmp:
                raise RuntimeError("XMP processing failed")
        except Exception as e:
            logging.error(f"XMP error: {e}")
            await callback.answer("❌ Ошибка при создании XMP", show_alert=True)
            return

        # Асинхронно создаем SNAP
        try:
            output_snap = await asyncio.to_thread(
                pm.create_snap_file,
                initials=user_data['idn'],
                input_xmp=output_xmp
            )
            if not output_snap:
                raise RuntimeError("SNAP creation failed")
        except Exception as e:
            logging.error(f"SNAP error: {e}")
            await callback.answer("❌ Ошибка при создании SNAP", show_alert=True)
            return

        # Отправка SNAP файла
        await callback.message.answer_document(
            FSInputFile(output_snap),
            caption=Texts.Caption.SNAP_IPTC
        )

        # Опционально: отправка XMP файла
        await callback.message.answer_document(
            FSInputFile(output_xmp),
            caption=Texts.Caption.XMP_IPTC
        )

        await callback.answer()

    except Exception as e:
        logging.error(f"Global error: {e}")
        await callback.answer("❌ Критическая ошибка при обработке", show_alert=True)