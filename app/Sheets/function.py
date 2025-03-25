import logging
import os

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
        "https://www.googleapis.com/auth/script.projects" # Добавлен новый scope для запуска функций в таблицах через API
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
    # wks = await agc.open("PhotoBot")
    # sh = await wks.worksheet(title='Лист1')
    wks = await agc.open("MainTable")
    sh = await wks.worksheet(title='ПУТЬ')
    # print("Spreadsheet URL: https://docs.google.com/spreadsheets/d/{0}".format(wks.id))
    cols = await sh.range(1, 1, sh.row_count, cols_to_sample)
    next_row = max([cell.row for cell in cols if cell.value]) + 1
    logging.info(f'нашли пустую строку: {next_row}')
    return next_row


async def next_available_row_special(sh, cols_to_sample=8) -> int:
    """Ищет первую пустую строку между '//##' и следующим '//sn??' с проверкой столбцов B-H."""
    agc = await agcm.authorize()
    wks = await agc.open("MainTable")
    sh = await wks.worksheet('ПУТЬ')

    # Получаем все данные листа
    all_data = await sh.get_all_values()

    section_ranges = []  # Список кортежей (start, end)
    last_section_start = -1

    # 1. Находим все пары "//##" → "//sn"
    for row_idx, row in enumerate(all_data):
        if len(row) == 0:
            continue
        col_a = row[0].strip()

        if col_a.startswith("//##"):
            last_section_start = row_idx
        elif col_a.startswith("//sn") and last_section_start != -1:
            section_ranges.append((last_section_start, row_idx))
            last_section_start = -1

    # 2. Проверяем строки между маркерами
    empty_candidates = []
    for start, end in section_ranges:
        for row_idx in range(start + 1, end):
            # Проверяем столбцы B-H (индексы 1-7 в данных)
            if len(all_data[row_idx]) < cols_to_sample:
                # Если строка короче 8 столбцов — считаем пустой
                empty_candidates.append(row_idx + 1)  # +1 для 1-индексации
                continue

            # Проверяем, все ли ячейки B-H пусты
            is_empty = all(
                cell.strip() == ""
                for cell in all_data[row_idx][1:8]  # Срезы B-H (индексы 1-7)
            )

            if is_empty:
                empty_candidates.append(row_idx + 1)  # Конвертация в 1-индексацию

    # 3. Возвращаем первую подходящую строку
    if empty_candidates:
        return min(empty_candidates)
    else:
        logging.info('Пустых строк между секциями не найдено, используем стандартный поиск.')
        return await next_available_row(sh)

async def number_row(data: dict) -> None:
    """Записывает данные в Google Sheets, обрабатывая ситуацию с несколькими серийными номерами."""
    agc = await agcm.authorize()
    # wks = await agc.open("PhotoBot")
    # sh = await wks.worksheet(title='Лист1')
    wks = await agc.open("MainTable")
    sh = await wks.worksheet(title='ПУТЬ')
    next_row = await next_available_row_special(sh)
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
        # wks = await agc.open("MainTable")
        # sh = await wks.worksheet("Расписание фото")
        wks = await agc.open("MainTable")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "СНЯТО")
        return "✅ СНЯТО успешно записано!", "СНЯТО"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None, None


async def write_cancel(row: int, col: int) -> Tuple[Optional[str], Optional[str]]:
    """Записывает 'ОТМЕНА' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        wks = await agc.open("MainTable")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "ОТМЕНА")
        return "✅ ОТМЕНА успешно записано!", "ОТМЕНА"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None, None

async def write_state(row: int, col: int) -> Tuple[Optional[str], Optional[str]]:
    """Записывает 'СНИМАЮТ' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        # wks = await agc.open("MainTable")
        # sh = await wks.worksheet("Расписание фото")
        wks = await agc.open("MainTable")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "СНИМАЮТ")
        return "✅ СНИМАЮТ успешно записано!", "СНИМАЮТ"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None, None

async def write_error(row: int, col: int) -> Tuple[Optional[str], Optional[str]]:
    """Записывает 'ОШИБКА' в ячейку под указанной"""
    try:
        agc = await agcm.authorize()
        # wks = await agc.open("MainTable")
        # sh = await wks.worksheet("Расписание фото")
        wks = await agc.open("MainTable")
        sh = await wks.worksheet("Расписание фото")
        await sh.update_cell(row + 1, col, "")
        return "✅ Отменил пометку успешно!", " НЕТ СТАТУСА"
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None, None


async def update_external_table_status(
        code: str,
        status: str,
        spreadsheet_name: str = "Расписание от Организаторов",
        sheet_name: str = "23_Марта"
) -> bool:
    """
    Записывает статус в ячейку слева от найденного кода во внешней таблице.
    Возвращает True при успешной записи, False при ошибках.
    """
    try:
        if not code:
            return False

        # Ищем код во внешней таблице
        matches = await find_text_code(
            text=code.strip(),
            spreadsheet_name=spreadsheet_name,
            sheet_name=sheet_name
        )

        if not matches:
            logging.info(f"Код {code} не найден во внешней таблице")
            return False

        # Обновляем ячейки
        agc = await agcm.authorize()
        org_table = await agc.open(spreadsheet_name)
        org_sheet = await org_table.worksheet(sheet_name)

        success = False
        for match in matches:
            target_row, target_col, _, _ = match

            if target_col > 1:
                await org_sheet.update_cell(
                    row=target_row,
                    col=target_col - 1,
                    value=status
                )
                success = True
            else:
                logging.warning(f"Невозможно записать в колонку 0 для кода: {code}")

        return success

    except WorksheetNotFound:
        logging.error(f"Таблица {spreadsheet_name} или лист {sheet_name} не найден")
        return False
    except Exception as e:
        logging.error(f"Ошибка обновления внешней таблицы: {str(e)}")
        return False


#-------------------------------------------------------------------------------------------------------------------
# Функции поиска ячеек
#-------------------------------------------------------------------------------------------------------------------

async def find_text_in_sheet(
        text: str,
        spreadsheet_name: str = "MainTable",
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
        spreadsheet_name: str = "MainTable",
        sheet_name: str = "Расписание фото",
        case_sensitive: bool = False
) -> List[Tuple[int, int, str]]:
    """
    Ищет ячейки, начинающиеся с указанного префикса.
    Возвращает список кортежей: (строка, колонка, полное значение).
    """
    agc: AsyncioGspreadClient = await agcm.authorize()
    sh = await agc.open(spreadsheet_name)
    wks: AsyncioGspreadWorksheet = await sh.worksheet(sheet_name)

    all_values = await wks.get_all_values()
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
#         spreadsheet_name: str = "MainTable",
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
        spreadsheet_name: str = "MainTable",
        sheet_name: str = "Расписание фото",
        case_sensitive: bool = False,
        exclude_words: Optional[List[str]] = None,
        include_values: Optional[List[str]] = None
) -> List[Tuple[int, int, str, List[str]]]:
    """Ищет ячейки по префиксу с фильтрацией и возвращает контекст."""
    agc: AsyncioGspreadClient = await agcm.authorize()
    sh= await agc.open(spreadsheet_name)
    wks: AsyncioGspreadWorksheet = await sh.worksheet(sheet_name)
    all_values = await wks.get_all_values()

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
        wks = await agc.open("MainTable")
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
        wks = await agc.open("MainTable")
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


async def get_sheet_url(
        spreadsheet_name: str,
        sheet_name: Optional[str] = None,
        include_sheet: bool = False
) -> str:
    """Возвращает URL таблицы с опциональным указанием листа"""
    agc = await agcm.authorize()
    sh = await agc.open(spreadsheet_name)

    if include_sheet and sheet_name:
        wks = await sh.worksheet(sheet_name)
        return f"https://docs.google.com/spreadsheets/d/{sh.id}/edit#gid={wks.id}"

    return f"https://docs.google.com/spreadsheets/d/{sh.id}/edit"


async def add_editor_to_sheet(email: str) -> bool:
    """Добавляет редактора через gspread-asyncio"""
    try:
        agc = await agcm.authorize()
        spreadsheet = await agc.open(os.getenv('TABLE_NAME_MANAGER'))

        # Логирование данных
        logging.info(f"Добавление редактора: {email}")
        logging.info(f"ID таблицы: {spreadsheet.id}")

        # Проверка существующих прав
        existing_perms = await spreadsheet.list_permissions()
        logging.info(f"Текущие права: {existing_perms}")

        if any(perm.get("emailAddress") == email for perm in existing_perms):
            logging.warning(f"Email {email} уже имеет доступ")
            return False

        # Добавляем права через клиент
        await agc.insert_permission(
            file_id=spreadsheet.id,
            value=email.strip(),
            perm_type="user",
            role="writer",
            notify=False
        )
        logging.info(f"Успешно добавлен: {email}")
        return True

    except Exception as e:
        logging.error(f"Ошибка добавления {email}: {str(e)}", exc_info=True)
        return False


# async def trigger_sync():
#     SCOPES = ['https://www.googleapis.com/auth/script.projects']
#     creds = service_account.Credentials.from_service_account_file(
#         'service-account.json',
#         scopes=SCOPES
#     )
#
#     # Делегирование прав (если нужно действовать от имени пользователя)
#     delegated_creds = creds.with_subject('nikryt@gmail.com')
#
#     response = requests.post(
#         f"https://script.googleapis.com/v1/scripts/{SCRIPT_ID}:run",
#         json={"function": "forceSync"},
#         headers={
#             "Authorization": f"Bearer {delegated_creds.token}",
#             "Content-Type": "application/json"
#         }
#     )
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
#         spreadsheet_name: str = "MainTable",
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
#         spreadsheet_name: str = "MainTable",
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
        spreadsheet_name: str = "MainTable",
        sheet_name: str = "Расписание фото"
) -> List[Tuple[int, int, str, List[str]]]:
    """
    Ищет текст в таблице и возвращает:
    - Координаты ячейки (строка, колонка)
    - Значение найденной ячейки
    - Список из трёх значений выше (от ближайшей к дальней)
    """
    agc: AsyncioGspreadClient = await agcm.authorize()
    sh = await agc.open(spreadsheet_name)
    wks: AsyncioGspreadWorksheet = await sh.worksheet(sheet_name)

    all_values = await wks.get_all_values()
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
