import re
import phonenumbers
import validators
from aiogram.fsm.context import FSMContext
from phonenumbers import NumberParseException, PhoneNumberFormat
from pathlib import Path
from typing import Tuple
from typing import Optional, List, Dict, Any
from Texts import Translit_en, Messages  # Импорт словаря транслитерации
from urllib.parse import urlparse


class ValidationError(Exception):
    """Базовое исключение для ошибок валидации"""
    pass


async def validate_name_ru(name: str) -> bool:
    """
    Валидация ФИО на русском языке

    Args:
        name (str): Входная строка с ФИО

    Returns:
        bool: True если соответствует шаблону, False в противном случае

    Examples:
        >>> validate_name_ru("Иванов Иван Иванович")
        True
        >>> validate_name_ru("Smith John")
        False
    """
    pattern = r"^[А-Яа-яЁё\-\' ]+$"
    return re.fullmatch(pattern, name) is not None


async def format_fio(name_ru: str) -> str:
    """
    Форматирование ФИО с правильным регистром

    Args:
        name_ru (str): Сырая строка с ФИО

    Returns:
        str: Отформатированное ФИО или пустая строка при ошибке

    Examples:
        >>> format_fio("иванов иван иванович")
        'Иванов Иван Иванович'
    """
    try:
        parts = [part.strip().capitalize() for part in name_ru.split() if part.strip()]
        return " ".join(parts) if parts else ""
    except (AttributeError, TypeError):
        return ""


async def validate_initials(initials: str) -> bool:
    """
    Валидация формата инициалов

    Args:
        initials (str): Строка с инициалами

    Returns:
        bool: True если соответствует формату XXX (3 латинские буквы)

    Examples:
        >>> validate_initials("ABC")
        True
        >>> validate_initials("A1C")
        False
    """
    clean = re.sub(r'[^A-Za-z]', '', initials).upper()
    return len(clean) == 3


async def transliterate_name(name_ru: str) -> str:
    """
    Транслитерация русского имени в английское по стандарту ГОСТ

    Args:
        name_ru (str): ФИО на русском языке

    Returns:
        str: Транслитерированное имя

    Examples:
        >>> transliterate_name("Иванов Иван")
        'Ivanov Ivan'
    """
    try:
        translit_dict = Translit_en.EN
        parts = []
        for part in name_ru.split():
            translit_part = ''.join(
                translit_dict.get(char, char) for char in part
            )
            if translit_part:
                formatted = translit_part[0].upper() + translit_part[1:].lower()
                parts.append(formatted)
        return ' '.join(parts)
    except (AttributeError, KeyError):
        raise ValidationError("Ошибка транслитерации имени")


async def generate_initials(name_en: str) -> str:
    """
    Генерация инициалов из английского имени

    Args:
        name_en (str): Полное имя на английском

    Returns:
        str: Инициалы в формате XXX

    Examples:
        >>> generate_initials("Ivanov Ivan")
        'IIV'
    """
    try:
        return ''.join([part[0].upper() for part in name_en.split() if part])
    except (AttributeError, TypeError):
        return ""


async def validate_media_group(files: List[Dict[str, Any]]) -> bool:
    """
    Валидация количества файлов в медиа-группе

    Args:
        files (list): Список файлов из медиа-группы

    Returns:
        bool: True если количество файлов ≤ 3, False в противном случае
    """
    return len(files) <= 3


async def format_phone(phone: str) -> Optional[str]:
    """
    Валидация и форматирование номера телефона

    Args:
        phone (str): Номер телефона в произвольном формате

    Returns:
        Optional[str]: Номер в формате E164 или None при ошибке

    Examples:
        >>> format_phone("+7 999 123-45-67")
        '+79991234567'
    """
    try:
        parsed = phonenumbers.parse(phone, "RU")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        return None
    except NumberParseException:
        return None

async def extract_valid_emails(email_str: str) -> list[str]:
    """Извлекает валидные email из строки"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, email_str)


# Фильтруем почтовые адреса из контактов
async def filter_emails(text: str) -> Optional[str]:
    """
    Удаляет все email-адреса из текста
    Возвращает:
    - Очищенный текст, если был ввод
    - None, если после очистки строка пустая
    """
    if not text:
        return None

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    cleaned_text = re.sub(email_pattern, '', text).strip()

    return cleaned_text if cleaned_text else None

#=======================================================================================================================
# Проверка путей операционных систем

async def validate_windows_path(path: str) -> Tuple[bool, str]:
    """
    Валидация пути Windows
    Возвращает (is_valid, error_message)
    """
    if not re.match(r'^(?:[a-zA-Z]:\\|\\\\[^\\]+\\)', path):
        return False, "❌ Неверный формат пути Windows. Пример: <code>C:\\Папка\\Файл.txt</code>"
    return True, ""


async def validate_unix_path(path: str, os_name: str = "macOS") -> Tuple[bool, str]:
    """
    Валидация Unix-путей с полной поддержкой:
    - Русских символов
    - Пробелов в именах
    - Переменных окружения
    - Относительных путей
    - Специальных символов (-_)
    """
    # Основное регулярное выражение
    unix_path_pattern = re.compile(
        r'^'
        r'(~)?'  # Домашняя директория
        r'((/?\$?[A-Za-z_][A-Za-z0-9_]*)'  # Переменные окружения
        r'|(\${[A-Za-z_][A-Za-z0-9_]*})'  # Переменные в фигурных скобках
        r'|([/.]{1,2}(?=/))'  # Относительные пути ./ и ../
        r'|([/][^\0<>:"|?*]+))'  # Основные компоненты пути
        r'([/][^\0<>:"|?*]*)*'  # Дополнительные компоненты
        r'$',
        re.UNICODE
    )

    # Проверка запрещенных символов
    if re.search(r'[\x00-\x1F\x7F<>:"|?*]', path):
        forbidden_chars = ''.join([chr(c) for c in range(0x20) if c != 0]) + '\x7F<>:"|?*'
        return False, f"❌ Путь содержит запрещенные символы: {forbidden_chars}"

    # Проверка общей структуры пути
    if not unix_path_pattern.fullmatch(path):
        examples = [
            "Абсолютный: <code>/Users/Иван/Документы/file.txt</code>",
            "С пробелом: <code>~/Мои документы/file.pdf</code>",
            "С переменными: <code>$HOME/Загрузки</code>",
            "Относительный: <code>../родительская папка/file</code>"
        ]
        return False, (
            f"❌ Неверный формат пути {os_name}.\n"
            f"Допустимые форматы:\n" + "\n".join(examples)
        )

    # Дополнительные проверки
    if path.count('/') > 100:  # Защита от слишком глубоких путей
        return False, "❌ Слишком сложная структура пути"

    return True, ""

async def normalize_path(path: str, os_type: str) -> str:
    """
    Нормализация пути для конкретной ОС
    """
    try:
        if os_type == 'windows':
            path = path.replace('/', '\\')
        else:
            path = path.replace('\\', '/')
            if path.startswith('~'):
                path = str(Path(path).expanduser())
        return path
    except Exception as e:
        raise ValueError(f"Ошибка нормализации пути: {str(e)}")


# Проверка путей операционных систем
#=======================================================================================================================

#=======================================================================================================================
# Проверка уникальности серийного номера присланых файлов

# async def check_duplicate_serial(state: FSMContext, new_serial: str) -> bool:
#     data = await state.get_data()
#     existing_serials = [data.get('serial1'), data.get('serial2'), data.get('serial3')]
#     return new_serial in existing_serials

async def check_duplicate_serial(state: FSMContext, new_serial: str) -> tuple:
    data = await state.get_data()
    for i in range(1, 4):
        if data.get(f'serial{i}') == new_serial:
            return True, data.get(f'photo{i}_name', 'неизвестный файл')
    return False, None

# async def validate_serial(serial: str, state: FSMContext) -> dict:
#     if serial == "SerialNumberNoFound":
#         return {'valid': False, 'message': Messages.SERIAL_NOT_FOUND_SINGLE}
#     if await check_duplicate_serial(state, serial):
#         return {'valid': False, 'message': Messages.SERIAL_DUPLICATE}
#     return {'valid': True, 'message': ''}

async def validate_serial(serial: str, state: FSMContext, current_file: str) -> dict:
    if serial == "SerialNumberNoFound":
        return {'valid': False, 'message': Messages.SERIAL_NOT_FOUND_SINGLE}

    is_duplicate, existing_file = await check_duplicate_serial(state, serial)
    if is_duplicate:
        return {
            'valid': False,
            'message': Messages.SERIAL_DUPLICATE.format(
                serial=serial,
                existing_file=existing_file
            )
        }
    return {'valid': True, 'message': ''}

# Проверка уникальности серийного номера присланых файлов
#=======================================================================================================================

#=======================================================================================================================
# Валидация почты и контактов


class ValidationError(Exception):
    pass


async def validate_contact(contact: str) -> bool:
    contact = contact.strip().lower()

    # Проверка email
    if validators.email(contact):
        return True

    # Проверка социальных упоминаний и URL
    social_domains = {
        'vk.com', 'facebook.com', 'instagram.com',
        't.me', 'telegram.me', 'vkontakte.ru'
    }

    # Проверка @username формата
    if re.search(r'(?:^|\s)(@[a-zA-Z0-9_]{5,32})\b', contact):
        return True

    # Проверка URL с извлечением домена
    url_candidate = re.sub(r'^.*?(http|www)', 'http', contact, 1)  # Удаляем текст до URL
    if not url_candidate.startswith(('http://', 'https://')):
        url_candidate = 'http://' + url_candidate

    if validators.url(url_candidate):
        parsed = urlparse(url_candidate)
        domain = parsed.hostname.replace('www.', '') if parsed.hostname else ''

        # Проверка домена в белом списке
        if domain in social_domains:
            return True

        # Проверка для Telegram (t.me/username)
        if domain == 't.me' and re.match(r'^/[a-zA-Z0-9_]{5,32}$', parsed.path):
            return True

    return False

# Валидация почты и контактов
#=======================================================================================================================
