from sqlalchemy import BigInteger, String, ForeignKey, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

import os
from dotenv import load_dotenv

load_dotenv()
engine =  create_async_engine(url=os.getenv('SQLALCHEMY_URL'))

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)

#class Category(Base):
class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=True)

class Item(Base):
    __tablename__ ='items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=True)
    nameRU: Mapped[str] = mapped_column(String(30), nullable=True)
    nameEN: Mapped[str] = mapped_column(String(30), nullable=True)
    idn: Mapped[str] = mapped_column(String(4), nullable=True)
    mailcontact: Mapped[str] = mapped_column(String(100), nullable=True)
    tel: Mapped[str] = mapped_column(String(30), nullable=True)
    serial1: Mapped[str] = mapped_column(String(30), nullable=True)
    serial2: Mapped[str] = mapped_column(String(30), nullable=True)
    serial3: Mapped[str] = mapped_column(String(30), nullable=True)
    photo1: Mapped[str] = mapped_column(String(30), nullable=True)
    photo2: Mapped[str] = mapped_column(String(30), nullable=True)
    photo3: Mapped[str] = mapped_column(String(30), nullable=True)
    role: Mapped[int] = mapped_column(ForeignKey('roles.id'), nullable=True)

    # Обратная связь с BildSettings
    bild_settings: Mapped[list["BildSettings"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan"
    )


class TempChanges(Base):
    __tablename__ = 'temp_changes'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    data: Mapped[str] = mapped_column(String(2000))


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String)

class BildSettings(Base):
    __tablename__ = "bild_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)  # Связь с Item
    os_type: Mapped[str] = mapped_column(String(30), nullable=False)
    raw_path: Mapped[str] = mapped_column(String(255), nullable=False)
    folder_format: Mapped[str] = mapped_column(String(255), nullable=False)

    # Связь с Item
    item: Mapped["Item"] = relationship(back_populates="bild_settings")

async  def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
