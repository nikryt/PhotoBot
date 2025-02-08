import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
# Для базы данных импортируем
from app.database.models import async_main

# Импортируем объект router из другого файла app/heandlers.py
from app.heandlers import router
# заменил на env
#from config import TOKEN
#from config import ID_GS

#Импорт из env
from dotenv import load_dotenv

async def main():
# Запуск функции базы данных в самом начале, для того что-бы при запуске бота создавались все таблицы
    await  async_main()
# Объекты переменные экземпляры класса
    load_dotenv()
    bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher() #Основной роутер обрабатывает входящие обновления, сообщения, calback
    #Вызываем метод include_router
    dp.include_router(router)
    await dp.start_polling(bot) #start_polling хэндлеры

# конструкция, которая запускает функцию Main
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('ВыключилиБота')