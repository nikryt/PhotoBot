import json
import logging

from app.database.models import async_session, TempChanges, Setting
from app.database.models import User, Role, Item
from sqlalchemy import select, update, delete, func
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
                nameRU=data["nameRU"],
                nameEN=data["nameEN"],
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

# # Функция получения данных о регистрации по tg_id пользователя
# async def get_item_by_tg_id(tg_id: int) -> Item | None:
#     async with async_session() as session:
#         return await session.scalar(select(Item).where(Item.name == str(tg_id)))

async def get_item_by_tg_id(tg_id: int) -> Item | None:
    async with async_session() as session:
        str_tg_id = str(tg_id)  # Явное преобразование в строку
        result = await session.execute(
            select(Item)
            .where(Item.name == str_tg_id)  # Сравнение как строки
            .order_by(Item.id.desc())
        )
        item = result.scalars().first()
        logging.info(f"Поиск пользователя: tg_id={str_tg_id}, результат={item}")
        return item

# async def get_item_by_tg_id(tg_id: int) -> Item | None:
#     async with async_session() as session:
#         # Преобразуем tg_id в строку
#         str_tg_id = str(tg_id)
#         # Ищем последнюю запись
#         result = await session.execute(
#             select(Item)
#             .where(Item.name == str_tg_id)
#             .order_by(Item.id.desc())
#         )
#         item = result.scalars().first()
#
#         # Если запись найдена, проверяем дубликаты
#         if item:
#             count = await session.execute(
#                 select(func.count())
#                 .where(Item.name == str_tg_id)
#             )
#             if count.scalar() > 1:
#                 await delete_duplicates(tg_id)
#                 # Повторно получаем запись после удаления дубликатов
#                 result = await session.execute(
#                     select(Item)
#                     .where(Item.name == str_tg_id)
#                     .order_by(Item.id.desc())
#                 )
#                 item = result.scalars().first()
#             logging.info(f"Поиск по tg_id={str_tg_id}. Найдено: {item}")
#         return item

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

# функция очистки дублей при запросе в личном меню на изменение данных.
async def delete_duplicates(tg_id: int):
    async with async_session() as session:
        str_tg_id = str(tg_id)
        # Получаем ID последней записи
        last_id = await session.execute(
            select(Item.id)
            .where(Item.name == str_tg_id)
            .order_by(Item.id.desc())
            .limit(1)
        )
        last_id = last_id.scalar()

        if last_id:
            # Удаляем все записи, кроме последней
            await session.execute(
                delete(Item)
                .where(Item.name == str_tg_id)
                .where(Item.id != last_id)
            )
            await session.commit()
            logging.info(f"Удалены дубликаты для tg_id={tg_id}. Сохранена запись ID={last_id}")

#=======================================================================================================================
# START Функции для обработки состояния регистрации
#=======================================================================================================================
async def get_registration_status() -> bool:
    # Возвращает текущий статус регистрации (по умолчанию True)
    async with async_session() as session:
        result = await session.execute(select(Setting.value).where(Setting.key == 'registration_enabled'))
        status = result.scalar()
        return status == 'true' if status else True

async def set_registration_status(enabled: bool):
    # Обновляет статус регистрации в базе
    async with async_session() as session:
        setting = await session.get(Setting, 'registration_enabled')
        if not setting:
            setting = Setting(key='registration_enabled', value=str(enabled).lower())
            session.add(setting)
        else:
            setting.value = str(enabled).lower()
        await session.commit()
#=======================================================================================================================
# END Функции для обработки состояния регистрации
#=======================================================================================================================