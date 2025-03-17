import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

# Функция валидации номера ☎️ Телефона
async def format_phone(phone: str) -> str:
    try:
        parsed = phonenumbers.parse(phone, "RU")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        return None
    except NumberParseException:
        return None