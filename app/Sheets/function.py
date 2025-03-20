import gspread_asyncio

from gspread.exceptions import WorksheetNotFound
from google.oauth2.service_account import Credentials
from typing import Optional, Tuple, List
from gspread_asyncio import AsyncioGspreadClient, AsyncioGspreadWorksheet

def get_creds() -> Credentials:
    """Возвращает учетные данные Google Sheets с нужными scope."""
    # To obtain a service account JSON file, follow these steps:
    # https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account
    # cs = Credentials.from_service_account_file("photobot-446116-eb367a5fb308.json")
    cs = Credentials.from_service_account_file("app/Sheets/photobot-446116-eb367a5fb308.json")
    scoped = cs.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    return scoped

agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)


#-------------------------------------------------------------------------------------------------------------------
# Функции записи данных
#-------------------------------------------------------------------------------------------------------------------

async def next_available_row(sh, cols_to_sample=8) -> int:
    """Ищет следующую пустую строку в указанном листе."""
    # Always authorize first.
    # If you have a long-running program call authorize() repeatedly.
    agc = await agcm.authorize()
    wks = await agc.open("PhotoBot")
    sh = await wks.worksheet(title='Лист1')
    # print("Spreadsheet URL: https://docs.google.com/spreadsheets/d/{0}".format(wks.id))
    cols = await sh.range(1, 1, sh.row_count, cols_to_sample)
    next_row = max([cell.row for cell in cols if cell.value]) + 1
    print('выполнили поиск')
    return next_row

async def number_row(data: dict) -> None:
    """Записывает данные в Google Sheets, обрабатывая ситуацию с несколькими серийными номерами."""
    agc = await agcm.authorize()
    wks = await agc.open("PhotoBot")
    sh = await wks.worksheet(title='Лист1')
    next_row = await next_available_row(sh)
    if data["serial1"] == 'NoSerial':
        values = [[f'//', f'{data["nameRU"]}', f'{data["nameEN"]}', f'{data["idn"]}', f'{data["mailcontact"]}', f'{data["tel"]}', f'{data["role"]}']]
        await sh.update(values, "A{}".format(next_row))
    if data ["serial1"] not in [None, 'NoSerial']:
        values = [[f'sn{data["serial1"]}', f'{data["nameRU"]}', f'{data["nameEN"]}', f'{data["idn"]}', f'{data["mailcontact"]}', f'{data["tel"]}', f'{data["role"]}']]
        await sh.update(values, "A{}".format(next_row))
        next_row += 1  # Вручную увеличиваем строку для следующих данных
    if data ["serial2"] not in [None, 'NoSerial']:
        values = [[f'sn{data["serial2"]}', f'{data["nameRU"]}', f'{data["nameEN"]}', f'{data["idn"]}', f'{data["mailcontact"]}', f'{data["tel"]}', f'{data["role"]}']]
        await sh.update(values, "A{}".format(next_row))
        next_row += 1  # Вручную увеличиваем строку для следующих данных
    if data ["serial3"] not in [None, 'NoSerial']:
        values = [[f'sn{data["serial3"]}', f'{data["nameRU"]}', f'{data["nameEN"]}', f'{data["idn"]}', f'{data["mailcontact"]}', f'{data["tel"]}', f'{data["role"]}']]
        await sh.update(values, "A{}".format(next_row))


async def write_done(row: int, col: int) -> Tuple[Optional[str], Optional[str]]:
    """Записывает 'СНЯТО' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "СНЯТО")
        return "✅ СНЯТО успешно записано!", "СНЯТО"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None

async def write_cancel(row: int, col: int) -> Tuple[Optional[str], Optional[str]]:
    """Записывает 'СНЯТО' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "ОТМЕНА")
        return "✅ ОТМЕНА успешно записано!", "ОТМЕНА"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None

async def write_state(row: int, col: int) -> Tuple[Optional[str], Optional[str]]:
    """Записывает 'СНИМАЮТ' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "СНИМАЮТ")
        return "✅ СНИМАЮТ успешно записано!", "СНИМАЮТ"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None

async def write_error(row: int, col: int) -> Tuple[Optional[str], Optional[str]]:
    """Записывает 'ОШИБКА' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "")
        return "✅ Отменил пометку успешно!", " НЕТ СТАТУСА"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None



#-------------------------------------------------------------------------------------------------------------------
# Функции поиска ячеек
#-------------------------------------------------------------------------------------------------------------------

async def find_text_in_sheet(
        text: str,
        spreadsheet_name: str = "Архипелаг 2024",
        sheet_name: str = "Расписание фото"
) -> List[Tuple[int, int, str]]:
    """
    Ищет все вхождения текста в указанной таблице и листе.
    Возвращает список координат (строка, колонка) в 1-индексации.
    """
    agc: AsyncioGspreadClient = await agcm.authorize()
    spreadsheet = await agc.open(spreadsheet_name)
    worksheet: AsyncioGspreadWorksheet = await spreadsheet.worksheet(sheet_name)

    # Получаем все данные листа
    all_values = await worksheet.get_all_values()

    # Подготавливаем текст для поиска
    search_text = text.strip().lower()
    matches = []

    # Ищем все совпадения
    for row_num, row in enumerate(all_values, start=1):
        for col_num, value in enumerate(row, start=1):
            if value.strip().lower().startswith(search_text.lower()) == search_text:
                # Добавляем оригинальное значение ячейки
                matches.append((row_num, col_num, value.strip()))


    return matches


async def find_cod(
        prefix: str,
        spreadsheet_name: str = "Архипелаг 2024",
        sheet_name: str = "Расписание фото",
        case_sensitive: bool = False
) -> List[Tuple[int, int, str]]:
    """
    Ищет ячейки, начинающиеся с указанного префикса.
    Возвращает список кортежей: (строка, колонка, полное значение).
    """
    agc: AsyncioGspreadClient = await agcm.authorize()
    spreadsheet = await agc.open(spreadsheet_name)
    worksheet: AsyncioGspreadWorksheet = await spreadsheet.worksheet(sheet_name)

    all_values = await worksheet.get_all_values()
    matches = []

    # Подготовка префикса для сравнения
    search_prefix = prefix.strip()
    if not case_sensitive:
        search_prefix = search_prefix.lower()

    for row_num, row in enumerate(all_values, start=1):
        for col_num, value in enumerate(row, start=1):
            # Очистка значения и проверка
            cleaned_value = value.strip()
            if not cleaned_value:
                continue

            # Приведение к нижнему регистру если нужно
            compare_value = cleaned_value if case_sensitive else cleaned_value.lower()
            target_prefix = search_prefix if case_sensitive else search_prefix.lower()

            if compare_value.startswith(target_prefix):
                matches.append((row_num, col_num, cleaned_value))

    return matches

# функция ищет все совпадения по началу слова и исключает точное совпадение без продолжения.

# async def find_all_text_code(
#         prefix: str,
#         spreadsheet_name: str = "Архипелаг 2024",
#         sheet_name: str = "Расписание фото",
#         case_sensitive: bool = False,
#         exclude_words: Optional[List[str]] = []  # Новый параметр для исключения # Устанавливаем пустой список по умолчанию
# ) -> List[Tuple[int, int, str, List[str]]]:
#     """
#     Ищет все ячейки с указанным префиксом и возвращает:
#     - Координаты (строка, колонка)
#     - Значение ячейки
#     - 3 значения выше (только непустые)
#
#     :param prefix: Префикс для поиска.
#     :param spreadsheet_name: Название таблицы.
#     :param sheet_name: Название листа.
#     :param case_sensitive: Учитывать регистр при поиске.
#     :param exclude_words: Список слов для исключения (проверка под найденным текстом).
#     :return: Список кортежей с результатами.
#     """
#     agc: AsyncioGspreadClient = await agcm.authorize()
#     spreadsheet = await agc.open(spreadsheet_name)
#     worksheet: AsyncioGspreadWorksheet = await spreadsheet.worksheet(sheet_name)
#
#     all_values = await worksheet.get_all_values()
#     search_prefix = prefix.strip()
#     matches = []
#
#     if not case_sensitive:
#         search_prefix_lower = search_prefix.lower()
#
#     for row_idx, row in enumerate(all_values):
#         for col_idx, value in enumerate(row):
#             current_value = value.strip()
#             if not current_value:
#                 continue
#
#             if case_sensitive:
#                 compare_value = current_value
#                 target_prefix = search_prefix
#             else:
#                 compare_value = current_value.lower()
#                 target_prefix = search_prefix_lower
#
#             # Проверяем, что значение начинается с префикса и не равно ему
#             if compare_value.startswith(target_prefix) and compare_value != target_prefix:
#                 # Проверяем ячейку под найденным текстом
#                 below_row_idx = row_idx + 1
#                 if below_row_idx < len(all_values) and col_idx < len(all_values[below_row_idx]):
#                     below_value = all_values[below_row_idx][col_idx].strip()
#                     if below_value in exclude_words:  # Проверяем на исключения
#                         continue  # Пропускаем этот результат
#
#                 # Сбор данных выше
#                 above_values = []
#                 for offset in range(1, 4):
#                     above_row_idx = row_idx - offset
#                     cell_value = ""
#
#                     if above_row_idx >= 0 and col_idx < len(all_values[above_row_idx]):
#                         cell_value = all_values[above_row_idx][col_idx].strip()
#
#                     above_values.append(cell_value)
#
#                 # Фильтрация пустых значений
#                 filtered_above = [v for v in above_values if v]
#
#                 if filtered_above:
#                     matches.append((
#                         row_idx + 1,
#                         col_idx + 1,
#                         current_value,
#                         filtered_above
#                     ))
#
#     return matches


async def find_all_text_code(
        prefix: str,
        spreadsheet_name: str = "Архипелаг 2024",
        sheet_name: str = "Расписание фото",
        case_sensitive: bool = False,
        exclude_words: Optional[List[str]] = None,
        include_values: Optional[List[str]] = None
) -> List[Tuple[int, int, str, List[str]]]:
    """Ищет ячейки по префиксу с фильтрацией и возвращает контекст."""
    agc: AsyncioGspreadClient = await agcm.authorize()
    spreadsheet = await agc.open(spreadsheet_name)
    worksheet: AsyncioGspreadWorksheet = await spreadsheet.worksheet(sheet_name)
    all_values = await worksheet.get_all_values()

    search_prefix = prefix.strip()
    matches = []

    if not case_sensitive:
        search_prefix = search_prefix.lower()

    for row_idx, row in enumerate(all_values):
        for col_idx, value in enumerate(row):
            current_value = value.strip()
            if not current_value:
                continue

            # Проверка префикса
            compare_value = current_value.lower() if not case_sensitive else current_value
            if not compare_value.startswith(search_prefix):
                continue
            if compare_value == search_prefix:
                continue

            # Проверка ячейки снизу
            below_value = ""
            if row_idx + 1 < len(all_values):
                below_row = all_values[row_idx + 1]
                if col_idx < len(below_row):
                    below_value = below_row[col_idx].strip()

            # Фильтрация
            if include_values:  # Приоритет у включения
                if below_value not in include_values:
                    continue
            elif exclude_words:  # Затем исключение
                if below_value in exclude_words:
                    continue

            # Сбор данных выше
            above_values = []
            for offset in range(1, 4):
                above_row_idx = row_idx - offset
                if above_row_idx >= 0 and col_idx < len(all_values[above_row_idx]):
                    cell_value = all_values[above_row_idx][col_idx].strip()
                    above_values.append(cell_value)

            filtered_above = [v for v in above_values if v]

            if filtered_above:
                matches.append((
                    row_idx + 1,  # +1 для перевода в 1-индексацию
                    col_idx + 1,
                    current_value,
                    filtered_above
                ))

    return matches


#======================================================================================================================
# Вспомогательные функции
#======================================================================================================================

# функция для получения значения ячейки
async def get_cell_value(row: int, col: int) -> Optional[str]:
    """Возвращает значение указанной ячейки"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")
        cell = await sh.cell(row, col)
        return cell.value
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None




async def get_above_values(row: int, col: int, count: int) -> List[str]:
    """Возвращает указанное количество значений сверху"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")

        start_row = max(1, row - count)
        end_row = row - 1
        if start_row > end_row:
            return []

        # Получаем диапазон ячеек
        range_name = f"{chr(64 + col)}{start_row}:{chr(64 + col)}{end_row}"
        values = await sh.get(range_name)

        return [item[0] for item in values if item]

    except Exception as e:
        print(f"Google Sheets error: {e}")
        return []


#-------------------------------------------------------------------------------------------------------------------
# Функция сохранения данных в TSV
#-------------------------------------------------------------------------------------------------------------------

async def save_sheet_as_tsv(
        filename: str,
        spreadsheet_name: str = "MainTable",
        sheet_name: str | None = None
) -> tuple[bool, str]:
    """
    Сохраняет указанный лист Google Sheets в файл TSV
    Возвращает кортеж (статус_сохранения, название_листа)
    """
    try:
        agc = await agcm.authorize()
        wks = await agc.open(spreadsheet_name)

        # Выбор листа
        if sheet_name:
            sh = await wks.worksheet(sheet_name)
        else:
            worksheets = await wks.worksheets()
            if not worksheets:
                raise ValueError("Таблица не содержит листов")
            sh = worksheets[0]

        # Получение данных
        data = await sh.get_all_values()

        # Сохранение в файл
        with open(filename, 'w', encoding='utf-8') as f:
            for row in data:
                f.write('\t'.join(row) + '\n')

        print(f"Успешно сохранено {len(data)} строк из листа '{sh.title}' в {filename}")
        return True, sh.title

    except WorksheetNotFound:
        print(f"Ошибка: лист с именем '{sheet_name}' не найден")
        raise
    except Exception as e:
        print(f"Ошибка при сохранении TSV: {str(e)}")
        raise


#   Функция ищет все совпадения с началом слова

# async def find_all_text_code(
#         prefix: str,
#         spreadsheet_name: str = "Архипелаг 2024",
#         sheet_name: str = "Расписание фото",
#         case_sensitive: bool = False
# ) -> List[Tuple[int, int, str, List[str]]]:
#     """
#     Ищет все ячейки с указанным префиксом и возвращает:
#     - Координаты (строка, колонка)
#     - Значение ячейки
#     - 3 значения выше (только непустые)
#     """
#     agc: AsyncioGspreadClient = await agcm.authorize()
#     spreadsheet = await agc.open(spreadsheet_name)
#     worksheet: AsyncioGspreadWorksheet = await spreadsheet.worksheet(sheet_name)
#
#     all_values = await worksheet.get_all_values()
#     search_prefix = prefix.strip()
#     matches = []
#
#     if not case_sensitive:
#         search_prefix_lower = search_prefix.lower()
#
#     for row_idx, row in enumerate(all_values):
#         for col_idx, value in enumerate(row):
#             current_value = value.strip()
#             if not current_value:
#                 continue
#
#             if case_sensitive:
#                 compare_value = current_value
#                 target_prefix = search_prefix
#             else:
#                 compare_value = current_value.lower()
#                 target_prefix = search_prefix_lower
#
#             # Проверяем, что значение начинается с префикса и не равно ему
#             if compare_value.startswith(target_prefix) and compare_value != target_prefix:
#                 # Сбор данных выше
#                 above_values = []
#                 for offset in range(1, 4):
#                     above_row_idx = row_idx - offset
#                     cell_value = ""
#
#                     if above_row_idx >= 0 and col_idx < len(all_values[above_row_idx]):
#                         cell_value = all_values[above_row_idx][col_idx].strip()
#
#                     above_values.append(cell_value)
#
#                 # Фильтрация пустых значений
#                 filtered_above = [v for v in above_values if v]
#
#                 if filtered_above:
#                     matches.append((
#                         row_idx + 1,
#                         col_idx + 1,
#                         current_value,
#                         filtered_above
#                     ))
#
#     return matches

# async def find_all_text_code(
#         prefix: str,
#         spreadsheet_name: str = "Архипелаг 2024",
#         sheet_name: str = "Расписание фото",
#         case_sensitive: bool = False
# ) -> List[Tuple[int, int, str, List[str]]]:
#     """
#     Ищет все ячейки, начинающиеся с указанного префикса, и возвращает:
#     - Координаты (строка, колонка) в 1-индексации
#     - Значение ячейки
#     - 3 значения выше в том же столбце
#     """
#     agc: AsyncioGspreadClient = await agcm.authorize()
#     spreadsheet = await agc.open(spreadsheet_name)
#     worksheet: AsyncioGspreadWorksheet = await spreadsheet.worksheet(sheet_name)
#
#     all_values = await worksheet.get_all_values()
#     search_prefix = prefix.strip()
#     matches = []
#
#     # Приводим к нижнему регистру если нужно
#     if not case_sensitive:
#         search_prefix = search_prefix.lower()
#
#     for row_idx, row in enumerate(all_values):
#         for col_idx, value in enumerate(row):
#             current_value = value.strip()
#             if not current_value:
#                 continue
#
#             # Проверяем начало строки
#             compare_value = current_value if case_sensitive else current_value.lower()
#             target_prefix = search_prefix if case_sensitive else search_prefix.lower()
#
#             if compare_value.startswith(target_prefix):
#                 gspread_row = row_idx + 1
#                 gspread_col = col_idx + 1
#
#                 # Собираем 3 ячейки выше
#                 above_values = []
#                 for offset in range(1, 4):
#                     above_row_idx = row_idx - offset
#
#                     if above_row_idx < 0:
#                         break
#
#                     cell_value = ""
#                     if col_idx < len(all_values[above_row_idx]):
#                         cell_value = all_values[above_row_idx][col_idx].strip()
#
#                     above_values.append(cell_value)
#
#                     above_values = []
#                     for offset in range(1, 4):
#                         above_row_idx = row_idx - offset
#
#                         if above_row_idx < 0:
#                             break
#
#                         cell_value = ""
#                         if col_idx < len(all_values[above_row_idx]):
#                             cell_value = all_values[above_row_idx][col_idx].strip()
#
#                         above_values.append(cell_value)
#
#                     # Фильтр: пропускаем если все 3 значения выше пустые
#                     if not all(val == "" for val in above_values):
#                         matches.append((
#                             gspread_row,
#                             gspread_col,
#                             current_value,
#                             above_values
#                         ))
#     return matches

#Ищем точное одно совпадение и выводим три строки выше
async def find_text_code(
        text: str,
        spreadsheet_name: str = "Архипелаг 2024",
        sheet_name: str = "Расписание фото"
) -> List[Tuple[int, int, str, List[str]]]:
    """
    Ищет текст в таблице и возвращает:
    - Координаты ячейки (строка, колонка)
    - Значение найденной ячейки
    - Список из трёх значений выше (от ближайшей к дальней)
    """
    agc: AsyncioGspreadClient = await agcm.authorize()
    spreadsheet = await agc.open(spreadsheet_name)
    worksheet: AsyncioGspreadWorksheet = await spreadsheet.worksheet(sheet_name)

    all_values = await worksheet.get_all_values()
    search_text = text.strip().lower()
    matches = []

    for row_idx, row in enumerate(all_values):
        for col_idx, value in enumerate(row):
            if value.strip().lower() == search_text:
                gspread_row = row_idx + 1  # Конвертация в 1-индексацию
                gspread_col = col_idx + 1
                current_value = value.strip()

                # Собираем 3 ячейки выше
                above_values = []
                for offset in range(1, 4):
                    above_row_idx = row_idx - offset

                    # Проверяем выход за границы таблицы
                    if above_row_idx < 0:
                        break

                    # Проверяем наличие столбца в строке
                    if col_idx >= len(all_values[above_row_idx]):
                        cell_value = ""
                    else:
                        cell_value = all_values[above_row_idx][col_idx].strip()

                    above_values.append(cell_value)

                matches.append((
                    gspread_row,
                    gspread_col,
                    current_value,
                    above_values
                ))

    return matches
