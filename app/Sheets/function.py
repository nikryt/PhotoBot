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


async def find_text_in_sheet(
        text: str,
        spreadsheet_name: str = "Архипелаг 2024",
        sheet_name: str = "Расписание фото"
) -> List[Tuple[int, int]]:
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
            if value.strip().lower() == search_text:
                matches.append((row_num, col_num))

    return matches

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
