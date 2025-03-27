import logging
import os
from pathlib import Path

import app.database.requests as rq
import app.Sheets.function as fu
from aiogram import Router, F, types
from aiogram.types import CallbackQuery, FSInputFile
from dotenv import load_dotenv


from app.Utils.XMP_edit import process_single_xmp

bild_router = Router()


@bild_router.callback_query(F.data == 'PM_data')
async def handle_pm_data_request(callback: types.CallbackQuery):
    """
    Обработчик запроса на генерацию XMP файла
    """
    try:
        user_id = callback.from_user.id

        # Получаем данные пользователя
        if not (user_data := await rq.get_user_data(user_id)):
            await callback.answer("❌ Ваши данные не найдены", show_alert=True)
            return

        # Проверяем обязательные поля
        if not all([user_data.get('idn'), user_data.get('mailcontact')]):
            await callback.answer("❌ Отсутствуют необходимые данные (инициалы или контакты)", show_alert=True)
            return

        # Пути к файлам
        base_dir = Path('app') / 'PhotoMechanic'
        source_file = base_dir / 'PM_Metadata_test2.XMP'

        # Обработка XMP
        if not (output_file := process_single_xmp(
                initials=user_data['idn'],
                contacts=user_data['mailcontact'],
                input_file=source_file
        )):
            raise RuntimeError("Не удалось обработать XMP файл")

        # Отправка файла пользователю
        await callback.message.answer_document(
            FSInputFile(output_file),
            caption="✅ Ваш XMP файл готов"
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка обработки запроса PM_data от {user_id}: {e}")
        await callback.answer("❌ Произошла ошибка при генерации файла", show_alert=True)