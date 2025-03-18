import json
import logging

from app.database.models import async_session, TempChanges
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
            logging.info(initials)
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

# Функция получения данных о роли по id в таблице
async def get_role_name(role_id: int) -> str | None:
    async with async_session() as session:
        role = await session.scalar(select(Role.name).where(Role.id == role_id))
        return role if role else "Не указана"

#-------------------------------------------------------------------------------------------------------------------
# Конец Функции получения данных
#-------------------------------------------------------------------------------------------------------------------



#-------------------------------------------------------------------------------------------------------------------
# Функции для обработки временных сохранений и подтверждения сохранения данных
#-------------------------------------------------------------------------------------------------------------------

async def save_temp_changes(tg_id: int, data: dict):
    async with async_session() as session:
        await session.execute(delete(TempChanges).where(TempChanges.tg_id == tg_id))
        session.add(TempChanges(tg_id=tg_id, data=json.dumps(data)))
        await session.commit()


async def get_temp_changes(tg_id: int) -> dict | None:
    async with async_session() as session:
        temp = await session.scalar(select(TempChanges).where(TempChanges.tg_id == tg_id))
        return json.loads(temp.data) if temp else None


async def apply_temp_changes(tg_id: int):
    async with async_session() as session:
        temp = await session.scalar(select(TempChanges).where(TempChanges.tg_id == tg_id))
        if not temp:
            return False

        data = json.loads(temp.data)
        item = await session.scalar(select(Item).where(Item.name == str(tg_id)))

        for field in ['nameRU', 'nameEN', 'idn', 'mailcontact', 'tel',
                      'role', 'serial1', 'serial2', 'serial3']:
            if field in data:
                setattr(item, field, data[field])

        await session.delete(temp)
        await session.commit()
        return True

async def del_temp_changes(user_id: int):
    async with async_session() as session:
        await session.execute(delete(TempChanges).where(TempChanges.tg_id == user_id))
        await session.commit()
        return True

# получаем id роли по ее названию
async def get_role_id_by_name(role_name: str) -> int | None:
    async with async_session() as session:
        role = await session.scalar(select(Role.id).where(Role.name == role_name))
        logging.info(role)
        return role

# получаем список всех фотогарфов.
async def get_all_photographers():
    async with async_session() as session:
        role_id = await get_role_id_by_name("Фотограф")
        if not role_id:
            return []

        result = await session.execute(
            select(Item.idn, Item.nameRU)
            .where(Item.role == role_id)
            .order_by(Item.nameRU)
        )
        logging.info(result)
        return result.all()  # Возвращаем список кортежей (idn, nameRU)