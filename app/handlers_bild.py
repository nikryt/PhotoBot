import os
import app.Sheets.function as fu
from aiogram import Router, F
from aiogram.types import CallbackQuery
from dotenv import load_dotenv

bild_router = Router()


@bild_router.callback_query(F.data.('PM_data'))