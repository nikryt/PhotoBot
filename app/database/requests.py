import logging

from app.database.models import async_session
from app.database.models import User, Role, Item
from sqlalchemy import select, update, delete
from sqlalchemy.orm import defer

# Записали при старте бота Telegram ID в таблицу User БД
async def set_user(tg_id):
    async with async_session() as session:
        user = await  session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()

async def get_roles():
    async with async_session() as session:
        return await session.scalars(select(Role))

# начал писать пока не закончил
async def set_item(data: dict):
    async with async_session() as session:
#         # проверяем есть ли уже запись от этого аккаунта в БД
#         name = await  session.scalar(select(Item).where(Item.name == data["tg_id"]))
#
# # Если нет еще записи от этого аккаунта то записываем в новую строчку
#         if not name:
            session.add(Item(
                name=data["tg_id"],
                nameRU=data["nameRu"],
                nameEN=data["nameEn"],
                idn=data["idn"],
                mailcontact=data["mailcontact"],
                tel=data["tel"],
                role=data["role"],
                serial1=data["serial1"],
                serial2=data["serial2"],
                serial3=data["serial3"],
                photo1=data["photofile1"],
                photo2=data["photofile2"],
                photo3=data["photofile3"])
            )
            await session.commit()


async def set_item_sn(serial: str):
    async with async_session() as session:
#         # проверяем есть ли уже запись от этого аккаунта в БД
#         name = await session.scalar(select(Item).where(Item.name == data["tg_id"]))
#
# # Если нет еще записи от этого аккаунта то записываем в новую строчку
#         if not name:
            session.add(Item(
                serial1=serial)
            )
            await session.commit()

# Пишем запрос на вывод данных
async def get_item():
    async with async_session() as session:
        items = await session.scalars(select(Item))
        return items

# Пишем удаление из базы данных
async def del_item(id):
    async with async_session() as session:
        await session.execute(delete(Item).where(Item.id == id))
        await session.commit()


#-------------------------------------------------------------------------------------------------------------------
# Функции получения данных
#-------------------------------------------------------------------------------------------------------------------

# Функция для получения инициалов из базы данных
async def get_initials(tg_id: int):
    async with async_session() as session:
        try:
            initials = await session.scalar(select(Item.idn).where(Item.name == tg_id))
            print(initials)
            return initials
        except Exception as e:
            print(f"Ошибка при получении инициалов: {e}")
            return None

# Функция для получения роли из базы данных
async def get_role(tg_id: int):
    async with async_session() as session:
        try:
            role = await session.scalar(select(Item.role).where(Item.name == tg_id))
            logging.info(f'Получена роль {role}')
            return role
        except Exception as e:
            logging.error(f"Ошибка при получении роли: {e}")
            return None

# Функция получения данных о регистрации по tg_id пользователя
async def get_item_by_tg_id(tg_id: int) -> Item | None:
    async with async_session() as session:
        return await session.scalar(select(Item).where(Item.name == str(tg_id)))