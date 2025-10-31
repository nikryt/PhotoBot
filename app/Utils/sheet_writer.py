import os
import logging
from typing import List, Dict, Tuple
import app.Sheets.function as fu


class SheetWriter:
    def __init__(self):
        # Используем конкретную таблицу "Расписание от Организаторов"
        self.spreadsheet_name = "Расписание от Организаторов"

    async def write_schedule_data(self, data: List[Dict], start_row: int, sheet_name: str = "Текущее") -> Tuple[
        bool, str]:
        """Записывает данные расписания в Google Sheets 'Расписание от Организаторов'"""
        try:
            success_count = 0
            error_count = 0

            for i, event_data in enumerate(data):
                row_number = start_row + i

                # Подготавливаем данные для записи
                values = [
                    event_data.get('Время', ''),
                    event_data.get('Место', ''),
                    event_data.get('Название', ''),
                    event_data.get('Спикеры', ''),
                    event_data.get('Описание', ''),
                    event_data.get('Трек', '')
                ]

                # Записываем строку
                success = await self._write_row(row_number, values, sheet_name)
                if success:
                    success_count += 1
                else:
                    error_count += 1

            message = f"✅ Успешно записано: {success_count} записей"
            if error_count > 0:
                message += f"\n❌ Ошибок: {error_count}"

            return True, message

        except Exception as e:
            logging.error(f"Error writing schedule data: {e}")
            return False, f"❌ Ошибка при записи в таблицу: {str(e)}"

    async def _write_row(self, row: int, values: List[str], sheet_name: str) -> bool:
        """Записывает одну строку в таблицу 'Расписание от Организаторов'"""
        try:
            agc = await fu.agcm.authorize()
            wks = await agc.open(self.spreadsheet_name)
            sh = await wks.worksheet(sheet_name)

            # Подготавливаем диапазон для записи (колонки A-F)
            range_start = f"A{row}"
            range_end = f"F{row}"

            await sh.update(f'{range_start}:{range_end}', [values])
            return True

        except Exception as e:
            logging.error(f"Error writing row {row} to {self.spreadsheet_name}: {e}")
            return False

    async def clear_range(self, start_row: int, end_row: int, sheet_name: str = "Текущее") -> bool:
        """Очищает диапазон строк в таблице"""
        try:
            agc = await fu.agcm.authorize()
            wks = await agc.open(self.spreadsheet_name)
            sh = await wks.worksheet(sheet_name)

            # Очищаем диапазон
            range_to_clear = f"A{start_row}:F{end_row}"
            await sh.batch_clear([range_to_clear])
            return True

        except Exception as e:
            logging.error(f"Error clearing range in {self.spreadsheet_name}: {e}")
            return False

    async def get_available_sheets(self) -> List[str]:
        """Возвращает список доступных листов в таблице"""
        try:
            agc = await fu.agcm.authorize()
            wks = await agc.open(self.spreadsheet_name)
            worksheets = await wks.worksheets()
            return [sheet.title for sheet in worksheets]
        except Exception as e:
            logging.error(f"Error getting available sheets: {e}")
            return []