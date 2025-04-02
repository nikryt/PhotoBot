import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
# Для базы данных импортируем
from app.database.models import async_main
# Импортируем объект router из другого файла app/handlers.py
from app.handlers import router
# Импортируем объект router из другого файла app/handlers_gr.py
from app.handles_gr import gr_router
from app.admin_private import admin_router
from app.handlers_manager import manager_router
from app.handlers_bild import bild_router
from app.handlers_help import help_router
# заменил на env
#from config import TOKEN
#from config import ID_GS

#Импорт из env
from dotenv import load_dotenv

from bot_cmd_list import private

async def main():
# Запуск функции базы данных в самом начале, для того что-бы при запуске бота создавались все таблицы.
    await  async_main()
# Объекты переменные экземпляры класса
    load_dotenv()
    bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher() #Основной роутер обрабатывает входящие обновления, сообщения, calback
    #Вызываем метод include_router
    dp.include_router(router) # этот роутер сработает первым
    dp.include_router(gr_router) # этот роутер сработает если первый не сработал
    dp.include_router(admin_router)
    dp.include_router(manager_router)
    dp.include_router(bild_router)
    dp.include_router(help_router)
    # Создаём кнопку меню с командами
    await  bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    # # Удаление кнопок
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())

    await dp.start_polling(bot) #start_polling хэндлеры

# конструкция, которая запускает функцию Main
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('ВыключилиБота')