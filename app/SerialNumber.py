import asyncio
from exiftool import ExifToolHelper

from aiogram import types


async def async_get_camera_serial_number(image_path):
    def sync_task():
        try:
            with ExifToolHelper() as et:
                metadata = et.get_metadata(image_path)[0]
                # Проверяем несколько возможных тегов для Canon
                serial = metadata.get("EXIF:SerialNumber") \
                         or metadata.get("MakerNotes:SerialNumber") \
                         or metadata.get("MakerNotes:CameraSerialNumber") \
                         or metadata.get("SerialNumber")
                if serial:
                    return str(serial)
                else:
                    print("Все доступные теги:", metadata.keys())
                    return "SerialNumberNoFound"
        except Exception as e:
            return f"Ошибка: {str(e)}"
    return await asyncio.to_thread(sync_task)


# Пример вызова
async def main_serial(message: types.Message):
    document = message.document
    file_name = document.file_name  # Получаем имя документа
    sender_name = message.from_user.username  # Получаем имя отправителя сообщения
    serial = await async_get_camera_serial_number(f'downloads/{sender_name}/{file_name}')
    print(serial)
    return serial

# Запуск асинхронного кода
# asyncio.run(main())

# file_path = "../downloads/downloads/BELOVERIK/ERIK0789.CR3"
# file_path = "../downloads/nikryt/KN3_7580.jpg"
