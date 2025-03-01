import asyncio
import gspread_asyncio
from gspread_asyncio import AsyncioGspreadClient, AsyncioGspreadSpreadsheet, AsyncioGspreadWorksheet

from google.oauth2.service_account import Credentials
from sqlalchemy.orm import defer
from typing import Optional, Tuple, List
from gspread_asyncio import AsyncioGspreadClient, AsyncioGspreadWorksheet

def get_creds():
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

async def next_available_row(sh, cols_to_sample=8):
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

async def number_row(data: dict):
    agc = await agcm.authorize()
    wks = await agc.open("PhotoBot")
    sh = await wks.worksheet(title='Лист1')
    next_row = await next_available_row(sh)
    if data["serial1"] == 'NoSerial':
        values = [[f'//', f'{data["nameRu"]}', f'{data["nameEn"]}', f'{data["idn"]}', f'{data["mailcontact"]}', f'{data["tel"]}', f'{data["role"]}']]
        await sh.update(values, "A{}".format(next_row))
    if data ["serial1"] not in [None, 'NoSerial']:
        values = [[f'sn{data["serial1"]}', f'{data["nameRu"]}', f'{data["nameEn"]}', f'{data["idn"]}', f'{data["mailcontact"]}', f'{data["tel"]}', f'{data["role"]}']]
        await sh.update(values, "A{}".format(next_row))
        next_row += 1  # Вручную увеличиваем строку для следующих данных
    if data ["serial2"] not in [None, 'NoSerial']:
        values = [[f'sn{data["serial2"]}', f'{data["nameRu"]}', f'{data["nameEn"]}', f'{data["idn"]}', f'{data["mailcontact"]}', f'{data["tel"]}', f'{data["role"]}']]
        await sh.update(values, "A{}".format(next_row))
        next_row += 1  # Вручную увеличиваем строку для следующих данных
    if data ["serial3"] not in [None, 'NoSerial']:
        values = [[f'sn{data["serial3"]}', f'{data["nameRu"]}', f'{data["nameEn"]}', f'{data["idn"]}', f'{data["mailcontact"]}', f'{data["tel"]}', f'{data["role"]}']]
        await sh.update(values, "A{}".format(next_row))


async def write_done(row: int, col: int) -> Optional[str]:
    """Записывает 'СНЯТО' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "СНЯТО")
        return "✅ СНЯТО успешно записано!"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None

async def write_cancel(row: int, col: int) -> Optional[str]:
    """Записывает 'СНЯТО' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "ОТМЕНА")
        return "✅ ОТМЕНА успешно записано!"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None

async def write_state(row: int, col: int) -> Optional[str]:
    """Записывает 'СНИМАЮТ' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "СНИМАЮТ")
        return "✅ СНИМАЮТ успешно записано!"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None

async def write_error(row: int, col: int) -> Optional[str]:
    """Записывает 'СНИМАЮТ' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("Архипелаг 2024")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "")
        return "✅ Отменил пометку успешно!"
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

async def find_all_text_code(
        prefix: str,
        spreadsheet_name: str = "Архипелаг 2024",
        sheet_name: str = "Расписание фото",
        case_sensitive: bool = False,
        exclude_words: Optional[List[str]] = []  # Новый параметр для исключения # Устанавливаем пустой список по умолчанию
) -> List[Tuple[int, int, str, List[str]]]:
    """
    Ищет все ячейки с указанным префиксом и возвращает:
    - Координаты (строка, колонка)
    - Значение ячейки
    - 3 значения выше (только непустые)

    :param prefix: Префикс для поиска.
    :param spreadsheet_name: Название таблицы.
    :param sheet_name: Название листа.
    :param case_sensitive: Учитывать регистр при поиске.
    :param exclude_words: Список слов для исключения (проверка под найденным текстом).
    :return: Список кортежей с результатами.
    """
    agc: AsyncioGspreadClient = await agcm.authorize()
    spreadsheet = await agc.open(spreadsheet_name)
    worksheet: AsyncioGspreadWorksheet = await spreadsheet.worksheet(sheet_name)

    all_values = await worksheet.get_all_values()
    search_prefix = prefix.strip()
    matches = []

    if not case_sensitive:
        search_prefix_lower = search_prefix.lower()

    for row_idx, row in enumerate(all_values):
        for col_idx, value in enumerate(row):
            current_value = value.strip()
            if not current_value:
                continue

            if case_sensitive:
                compare_value = current_value
                target_prefix = search_prefix
            else:
                compare_value = current_value.lower()
                target_prefix = search_prefix_lower

            # Проверяем, что значение начинается с префикса и не равно ему
            if compare_value.startswith(target_prefix) and compare_value != target_prefix:
                # Проверяем ячейку под найденным текстом
                below_row_idx = row_idx + 1
                if below_row_idx < len(all_values) and col_idx < len(all_values[below_row_idx]):
                    below_value = all_values[below_row_idx][col_idx].strip()
                    if below_value in exclude_words:  # Проверяем на исключения
                        continue  # Пропускаем этот результат

                # Сбор данных выше
                above_values = []
                for offset in range(1, 4):
                    above_row_idx = row_idx - offset
                    cell_value = ""

                    if above_row_idx >= 0 and col_idx < len(all_values[above_row_idx]):
                        cell_value = all_values[above_row_idx][col_idx].strip()

                    above_values.append(cell_value)

                # Фильтрация пустых значений
                filtered_above = [v for v in above_values if v]

                if filtered_above:
                    matches.append((
                        row_idx + 1,
                        col_idx + 1,
                        current_value,
                        filtered_above
                    ))

    return matches


#-------------------------------------------------------------------------------------------------------------------
# Функция сохранения данных в TSV
#-------------------------------------------------------------------------------------------------------------------

async def save_sheet_as_tsv(
        sheet_name: str,
        filename: str,
        spreadsheet_name: str = "MainTable"
):
    """
    Сохраняет указанный лист Google Sheets в файл TSV

    :param sheet_name: Название листа для сохранения
    :param filename: Имя выходного файла
    :param spreadsheet_name: Название таблицы в Google Sheets (по умолчанию "PhotoBot")
    """
    try:
        agc = await agcm.authorize()
        wks = await agc.open(spreadsheet_name)
        sh = await wks.worksheet(sheet_name)

        data = await sh.get_all_values()

        with open(filename, 'w', encoding='utf-8') as f:
            for row in data:
                f.write('\t'.join(row) + '\n')

        print(f"Успешно сохранено {len(data)} строк в {filename}")
        return True

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

# вызов функции
# async def main():
#     results = await find_text_code("KNA")
#
#     for row, col, value, above in results:
#         print(f"Найдено в [{row}, {col}]: {value}")
#         print("Значения выше:")
#         for i, val in enumerate(above, start=1):
#             print(f"  {i} строкой выше: {val}")


# async def find_text_in_sheet(
#         text: str,
#         spreadsheet_name: str = "Архипелаг 2024",
#         sheet_name: str = "Расписание фото"
# ) -> Optional[Tuple[int, int]]:
#     """
#     Ищет текст в указанной таблице и листе.
#     Возвращает координаты (строка, колонка) в 1-индексации или None.
#     """
#     agc: AsyncioGspreadClient = await agcm.authorize()
#     spreadsheet = await agc.open(spreadsheet_name)
#     worksheet: AsyncioGspreadWorksheet = await spreadsheet.worksheet(sheet_name)
#
#     # Получаем все данные листа
#     all_values = await worksheet.get_all_values()
#
#     # Ищем точное совпадение с учетом пробелов
#     search_text = text.strip().lower()
#
#     for row_num, row in enumerate(all_values, start=1):
#         for col_num, value in enumerate(row, start=1):
#             if value.strip().lower() == search_text:
#                 return (row_num, col_num)
#
#     return None

# async def example_usage():
#     # Поиск в таблице по умолчанию
#     result = await find_text_in_sheet("Персональный код AIV")
#     print(f"Результат поиска: {result}")

    # # Поиск в другой таблице и листе
    # result_custom = await find_text_in_sheet(
    #     text="Другой текст",
    #     spreadsheet_name="ДругаяТаблица",
    #     sheet_name="ДругойЛист"
    # )
    # print(f"Кастомный поиск: {result_custom}")

# Запуск асинхронного кода
# import asyncio
# asyncio.run(example_usage())

# async def number_row(item: dict):
#     agc = await agcm.authorize()
#     wks = await agc.open("PhotoBot")
#     sh = await wks.worksheet(title='Лист1')
#     next_row = await next_available_row(sh)
#     values = [[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']]
#     await sh.update(values, "A{}".format(next_row))
#     # await  sh.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], "A{}".format(next_row))

# #--------------------------------------------------------------------------------------
# #
# #   Работает но не ассинхронно
# #
# #--------------------------------------------------------------------------------------
# # gc = gspread.service_account(filename="photobot-446116-eb367a5fb308.json")
# gc = gspread.service_account(filename="app/Sheets/photobot-446116-eb367a5fb308.json")
# wks = gc.open("PhotoBot").sheet1
# def next_available_row(sheet, cols_to_sample=2):
#   # looks for empty row based on values appearing in 1st N columns
#   cols = sheet.range(1, 1, sheet.row_count, cols_to_sample)
#   return max([cell.row for cell in cols if cell.value]) + 1
#
# next_row = next_available_row(wks)
# print(next_row)
#
# #insert on the next available row
# # wks.update_acell("A{}".format(next_row), 'somevar')
# # wks.update_acell("B{}".format(next_row), 'somevar2')
#
# #--------------------------------------------------------------------------------------
# #
# #   Работает но не ассинхронно
# #
# #--------------------------------------------------------------------------------------
#
# # # Update a range of cells using the top left corner address
# # wks.update([[1, 2, 3,4,5], [6, 7]], 'A2')
#
# # # Or update a single cell
# # wks.update_acell('B42', "it's down there somewhere, let me take another look.")
# #
# # # Format the header
# # wks.format('A1:F1', {'textFormat': {'bold': True}})
# #
# # # def updateSH():
# # #     gc = gspread.service_account(filename='photobot-446116-eb367a5fb308.json')
# # #     wks = gc.open("PhotoBot").sheet1
# # #     wks.update([[1, 2, 3, 4, 5], [6, 7]], 'A2')
