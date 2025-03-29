import re
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
from typing import Optional, List, Dict, Any
from Texts import Translit_en  # Импорт словаря транслитерации


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