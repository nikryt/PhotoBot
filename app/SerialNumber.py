import asyncio
from exiftool import ExifToolHelper

from aiogram import types
#
# async def async_get_camera_serial_number(image_path):
#     def sync_task():
#         try:
#             with open(image_path, 'rb') as f:
#                 tags = exifread.process_file(f, details=False)
#                 return str(tags.get('EXIF BodySerialNumber', 'Серийный номер не найден'))
#         except Exception as e:
#             return f"Ошибка: {str(e)}"
#
#     # Запуск синхронной задачи в отдельном потоке
#     result = await asyncio.to_thread(sync_task)
#     return result

# Новая функция которая находит серийник в NEF
# async def async_get_camera_serial_number(image_path):
#     def sync_task():
#         try:
#             with open(image_path, 'rb') as f:
#                 # Обрабатываем EXIF с детализацией и включаем MakerNotes
#                 tags = exifread.process_file(f, details=True)
#
#                 # Проверяем несколько возможных тегов для серийного номера
#                 serial_tags = [
#                     'EXIF BodySerialNumber',  # Стандартный EXIF тег
#                     'MakerNote SerialNumber',  # Возможный тег в MakerNotes
#                     'Image SerialNumber',  # Альтернативный тег
#                     'MakerNote SerialNO',  # Вариант для Nikon
#                     'EXIF CameraSerialNumber'  # Дополнительный вариант
#                 ]
#
#                 for tag in serial_tags:
#                     if tag in tags:
#                         return str(tags[tag])
#
#                 # Если ни один тег не найден, выводим все доступные теги для диагностики
#                 print("Available tags:", tags.keys())
#                 return "Серийный номер не найден в EXIF данных"
#
#         except Exception as e:
#             return f"Ошибка: {str(e)}"
#
#     return await asyncio.to_thread(sync_task)


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
