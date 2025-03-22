import os
import app.Sheets.function as fu
from aiogram import Router, F
from aiogram.types import CallbackQuery
from dotenv import load_dotenv

manager_router = Router()
load_dotenv()
TABLE_NAME_M = str(os.getenv('TABLE_NAME_MANAGER'))
TABLE_NAME_P = str(os.getenv('TABLE_NAME_SHEDULE_PUBLIC'))
LIST_NAME = str(os.getenv('NAME_LIST_MANAGER_PHOTO'))


@manager_router.callback_query(F.data.in_({"tables_photo", "tables_shedule"}))
async def handle_table_callback(callback: CallbackQuery):
    try:
        if callback.data == "tables_photo":
            # Для таблицы менеджера: ссылка на конкретный лист
            url = await fu.get_sheet_url(
                spreadsheet_name=TABLE_NAME_M,
                include_sheet=True
            )
            text = "📌 Таблица организаторов"

        elif callback.data == "tables_shedule":
            # Для публичного расписания: общая ссылка на таблицу
            url = await fu.get_sheet_url(
                spreadsheet_name=TABLE_NAME_P,
                sheet_name=LIST_NAME,
                include_sheet=False
            )
            text = "📅 Публичное расписание фотографов"

        await callback.message.answer(f"{text}:\n{url}")

    except Exception as e:
        await callback.message.answer("🔴 Ошибка при получении таблицы")
        print(f"Error: {e}")

    await callback.answer()