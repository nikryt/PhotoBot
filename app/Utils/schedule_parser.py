import pandas as pd
import io
import logging
from typing import List, Dict, Tuple
import csv


class ScheduleParser:
    def __init__(self):
        self.required_columns = ['Время', 'Место', 'Название', 'Спикеры', 'Описание', 'Трек']

    async def parse_file(self, file_content: bytes, filename: str) -> Tuple[bool, List[Dict], str]:
        """Парсит файл расписания и возвращает данные"""
        try:
            filename_lower = filename.lower()

            if filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
                return await self._parse_excel(file_content)
            elif filename_lower.endswith('.csv'):
                return await self._parse_csv(file_content)
            else:
                return False, [], "❌ Формат файла не поддерживается. Используйте .xlsx, .xls или .csv"

        except Exception as e:
            logging.error(f"Error parsing schedule file: {e}")
            return False, [], f"❌ Ошибка при парсинге файла: {str(e)}"

    async def _parse_excel(self, file_content: bytes) -> Tuple[bool, List[Dict], str]:
        """Парсит Excel файл"""
        try:
            # Читаем Excel файл
            df = pd.read_excel(io.BytesIO(file_content))

            # Нормализуем названия колонок
            df.columns = [str(col).strip() for col in df.columns]

            # Ищем нужные колонки
            column_mapping = await self._find_columns(df)

            if not column_mapping:
                return False, [], "❌ Не удалось определить структуру данных в файле"

            # Обрабатываем данные
            processed_data = []
            for index, row in df.iterrows():
                if await self._is_valid_row(row, column_mapping):
                    event_data = {}

                    for sheet_col, data_col in column_mapping.items():
                        value = row[data_col]
                        # Преобразуем в строку и очищаем
                        if pd.isna(value):
                            value = ""
                        else:
                            value = str(value).strip()
                        event_data[sheet_col] = value

                    processed_data.append(event_data)

            if not processed_data:
                return False, [], "❌ Не найдено подходящих данных для импорта"

            return True, processed_data, f"✅ Найдено {len(processed_data)} записей для импорта"

        except Exception as e:
            logging.error(f"Error in _parse_excel: {e}")
            return False, [], f"❌ Ошибка при чтении Excel файла: {str(e)}"

    async def _parse_csv(self, file_content: bytes) -> Tuple[bool, List[Dict], str]:
        """Парсит CSV файл"""
        try:
            # Пробуем разные кодировки и разделители
            encodings = ['utf-8', 'windows-1251', 'cp1251']

            for encoding in encodings:
                try:
                    file_text = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return False, [], "❌ Не удалось определить кодировку файла"

            # Пробуем разные разделители
            separators = [';', ',', '\t']
            df = None

            for sep in separators:
                try:
                    df = pd.read_csv(io.StringIO(file_text), sep=sep)
                    if len(df.columns) > 1:  # Если нашлось больше одной колонки
                        break
                except:
                    continue

            if df is None or len(df.columns) <= 1:
                return False, [], "❌ Не удалось прочитать структуру CSV файла"

            # Дальнейшая обработка аналогична Excel
            df.columns = [str(col).strip() for col in df.columns]
            column_mapping = await self._find_columns(df)

            if not column_mapping:
                return False, [], "❌ Не удалось определить структуру данных в CSV файле"

            processed_data = []
            for index, row in df.iterrows():
                if await self._is_valid_row(row, column_mapping):
                    event_data = {}

                    for sheet_col, data_col in column_mapping.items():
                        value = row[data_col]
                        if pd.isna(value):
                            value = ""
                        else:
                            value = str(value).strip()
                        event_data[sheet_col] = value

                    processed_data.append(event_data)

            if not processed_data:
                return False, [], "❌ Не найдено подходящих данных для импорта"

            return True, processed_data, f"✅ Найдено {len(processed_data)} записей для импорта"

        except Exception as e:
            logging.error(f"Error in _parse_csv: {e}")
            return False, [], f"❌ Ошибка при чтении CSV файла: {str(e)}"

    async def _find_columns(self, df) -> Dict[str, str]:
        """Находит соответствие колонок в файле и целевой таблице"""
        column_mapping = {}
        available_columns = list(df.columns)

        # Ключевые слова для поиска колонок
        column_keywords = {
            'Время': ['время', 'time', 'времени', 'расписание'],
            'Место': ['место', 'location', 'локация', 'place', 'адрес'],
            'Название': ['название', 'event', 'мероприятие', 'заголовок', 'title', 'name'],
            'Спикеры': ['спикеры', 'speaker', 'докладчик', 'преподаватель', 'лектор'],
            'Описание': ['описание', 'description', 'детали', 'информация'],
            'Трек': ['трек', 'track', 'направление', 'stream']
        }

        for target_col, keywords in column_keywords.items():
            found = False
            for available_col in available_columns:
                if available_col in column_mapping.values():
                    continue

                available_col_lower = str(available_col).lower()
                for keyword in keywords:
                    if keyword in available_col_lower:
                        column_mapping[target_col] = available_col
                        found = True
                        break
                if found:
                    break

            # Если не нашли по ключевым словам, берем первую доступную колонку
            if not found and available_columns:
                for available_col in available_columns:
                    if available_col not in column_mapping.values():
                        column_mapping[target_col] = available_col
                        break

        return column_mapping

    async def _is_valid_row(self, row, column_mapping) -> bool:
        """Проверяет, является ли строка валидной для импорта"""
        # Строка считается валидной, если есть хотя бы время и название
        has_time = False
        has_name = False

        for target_col, data_col in column_mapping.items():
            value = row[data_col]
            if pd.notna(value) and str(value).strip():
                if target_col == 'Время':
                    has_time = True
                elif target_col == 'Название':
                    has_name = True

        return has_time and has_name


# Добавим в конец класса ScheduleParser метод для проверки структуры данных
async def validate_data_structure(self, data: List[Dict]) -> Tuple[bool, str]:
    """Проверяет структуру данных перед записью"""
    if not data:
        return False, "Нет данных для проверки"

    required_fields = ['Время', 'Название']
    for i, item in enumerate(data):
        for field in required_fields:
            if not item.get(field, '').strip():
                return False, f"Запись {i + 1} не содержит обязательное поле '{field}'"

    return True, "✅ Структура данных корректна"