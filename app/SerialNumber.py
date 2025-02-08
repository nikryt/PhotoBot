import asyncio
import exifread

from aiogram import types

async def async_get_camera_serial_number(image_path):
    def sync_task():
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                return str(tags.get('EXIF BodySerialNumber', 'Серийный номер не найден'))
        except Exception as e:
            return f"Ошибка: {str(e)}"

    # Запуск синхронной задачи в отдельном потоке
    result = await asyncio.to_thread(sync_task)
    return result

# Пример вызова
async def main(message: types.Message):
    document = message.document
    file_name = document.file_name  # Получаем имя документа
    sender_name = message.from_user.username  # Получаем имя отправителя сообщения
    serial = await async_get_camera_serial_number(f'downloads/{sender_name}/{file_name}')
    print(serial)
    return serial

# Запуск асинхронного кода
# asyncio.run(main())

# file_path = "../downloads/nikryt/2024-10-01_12-27-23_KN2_4220.jpg"
# file_path = "../downloads/nikryt/KN3_7580.jpg"
