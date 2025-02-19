from string import punctuation

from aiogram import F, Router, types, Bot

gr_router = Router()


restricted_worlds = {'сука', 'canon', 'sony'}



def clean_text(text: str):
    """функция удаляет все знаки препинания из текста"""
    return text.translate(str.maketrans('', '', punctuation))

@gr_router.message()
async def cleaner(message: types.Message):
    """функция удаляет сообщения из списка и предупреждает пользователя"""
    if restricted_worlds.intersection(clean_text(message.text.lower()).split()):
        await message.answer(f'{message.from_user.first_name}, не ругайся в чате!')
        await message.delete()
        # await message.chat.ban(message.from_user.id)