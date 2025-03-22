from aiogram import F, Router, types, Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.Filters.chat_types import ChatTypeFilter, IsAdmin  # импортировали наши личные фильтры
from app.generate import ai_generate
from app.handlers import Gen, save_document

import app.keyboards as kb
import app.database.requests as rq
import app.Sheets.function as fu
import app.Utils.validators as vl


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

@admin_router.message(Command("admin"))
async def admin_keyboard(message: types.Message):
    status = await rq.get_registration_status()
    await message.answer(
        "Панель администратора:",
        reply_markup=await kb.admin_keyboard(status)
    )


#=======================================================================================================================
# START Получить ID медиа данных
#=======================================================================================================================

# отвечаем на фото его ID
@admin_router.message(F.photo)
async def get_photo(message: Message):
    await message.answer(f'ID фото: {message.photo[-1].file_id}')

# Отвечаем на документ его ID
@admin_router.message(F.document)
async def get_document(message: Message):
    await message.answer(f'ID документа: {message.document.file_id}')

async def process_document(message: types.Message, bot: Bot):
    await save_document(message, bot)


# Отвечаем на стикер его ID и ID чата
@admin_router.message(F.sticker)
async def check_sticker(message: Message):
    await message.answer(f'ID стикера: {message.sticker.file_id}')
    await message.answer(f'id чата: {message.from_user.id, message.chat.id}')

#=======================================================================================================================
# END Получить ID медиа данных
#=======================================================================================================================



#Выводим данные из базы по запросу
@admin_router.message(F.text == "Можно всех посмотреть")
async def view_all_items(message: types.Message):
    for item in await rq.get_item():
        try:
            await message.answer_document(document=item.serial1,
                                          caption=f'🪪 ФИО ru: {item.nameRU}\n'
                                                  f'🪪 ФИО en: {item.nameEN}\n'
                                                  f'🪪 Инициалы: {item.idn}\n'
                                                  f'📫 Контакты: {item.mailcontact}\n'
                                                  f'☎️ Телефон: {item.tel}\n'
                                                  f'🪆 Роль: {item.role}',
                                          protect_content=True,
                                          reply_markup=await kb.edit_item(btns={
                                              'Удалить': f'delete_{item.id}',
                                              'Изменить': f'change_{item.id}'})
                                          )
            # запись просто в ячейку
            # sh.wks.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], 'A2')
            # запись просто в последнюю свободную ячейку,но ячейка находится только при старте боета, нужно похоже ассинхронную функцию делать
            # await sh.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], "A{}".format(sh.next_row))

        except TelegramBadRequest:
            await message.answer(text=f'🪪 ФИО ru: {item.nameRU}\n'
                                      f'🪪 ФИО en: {item.nameEN}\n'
                                      f'🪪 Инициалы: {item.idn}\n'
                                      f'📫 Контакты: {item.mailcontact}\n'
                                      f'☎️ Телефон: {item.tel}\n'
                                      f'🪆 Роль: {item.role}',
                                 protect_content=True,
                                 message_effect_id="5046589136895476101",
                                 reply_markup=await kb.edit_item(btns={
                                     '🗑️ Удалить': f'delete_{item.id}',
                                     '✏️ Изменить': f'change_{item.id}'}))
            # запись просто в ячейку
            # sh.wks.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], 'A2')
            # запись просто в последнюю свободную ячейку,но ячейка находится только при старте боета, нужно похоже ассинхронную функцию делать
            # await fu.number_row(item)
            # await fu.sh.update([[f'{item.nameRU}',f'{item.nameEN}',f'{item.idn}',f'{item.mailcontact}',f'{item.tel}',f'{item.role}']], "A{}".format(sh.next_row))

    await message.answer("Вот все, любуйся")

#Ловим нажатие на инлайн кнопки по редактированию или удалению
@admin_router.callback_query(F.data.startswith('delete_'))
async def delete_item(callback: CallbackQuery):
    item_id = callback.data.split("_")[-1]
    await  rq.del_item(int(item_id))
    await callback.answer(text=f'Запись удалена')
    await callback.message.answer(text=f'Запись удалена')



#=======================================================================================================================
# DeepSeek
#=======================================================================================================================
@admin_router.message(F.text == "поговори", )
async def deepseek(message: Message, state: FSMContext):
    await message.answer('Напиши что ты хочешь?')
    await state.set_state(Gen.result)

@admin_router.message(Gen.result)
async def generating(message: Message, state: FSMContext):
    await state.set_state(Gen.wait)
    responses = await ai_generate(message.text)
    await message.answer(responses)
    await state.clear()

@admin_router.message(Gen.wait)
async def stop_flood(message: Message):
    await message.answer('Подожди ты, не так быстро, эй!')
#=======================================================================================================================
# DeepSeek
#=======================================================================================================================



#=======================================================================================================================
# START Открытие или закрытие регистрации
#=======================================================================================================================
@admin_router.callback_query(F.data == 'toggle_registration')
async def toggle_registration(callback: CallbackQuery):
    current_status = await rq.get_registration_status()
    new_status = not current_status
    await rq.set_registration_status(new_status)

    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=await kb.admin_keyboard(new_status)
    )
    await callback.answer(f"Регистрация {'включена' if new_status else 'выключена'}!")
#=======================================================================================================================
# END Открытие или закрытие регистрации
#=======================================================================================================================

#=======================================================================================================================
# START Права на доступ к таблице для менеджера
#=======================================================================================================================
@admin_router.callback_query(F.data == "add_editors_list")
async def show_editors_list(callback: CallbackQuery):
    editors = await rq.get_editors()

    if not editors:
        await callback.message.answer("❌ Нет кандидатов для добавления")
        return

    await callback.message.answer(
        "📋 Список кандидатов в редакторы:",
        reply_markup=await kb.editors_list_keyboard(editors)
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("confirm_editor_"))
async def confirm_editor(callback: CallbackQuery):
    editor_id = int(callback.data.split("_")[-1])
    editor = await rq.get_editor_by_id(editor_id)

    if not editor:
        await callback.message.answer("❌ Пользователь не найден")
        return

    valid_emails = vl.extract_valid_emails(editor.mailcontact)
    if not valid_emails:
        await callback.message.answer("❌ Нет валидных email в профиле")
        return

    await callback.message.answer(
        f"Добавить пользователя:\n <b>{editor.nameRU}</b>\n"
        f"Email: <code>{valid_emails[0]}</code> в редакторы?",
        parse_mode=ParseMode.HTML,
        reply_markup=await kb.confirmation_keyboard(editor_id, editor.nameRU)
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("add_editor_"))
async def add_editor_final(callback: CallbackQuery):
    editor_id = int(callback.data.split("_")[-1])
    editor = await rq.get_editor_by_id(editor_id)

    if not editor:
        await callback.message.answer("❌ Ошибка: пользователь не найден")
        return

    success = await fu.add_editor_to_sheet(editor.mailcontact)
    if success:
        await callback.message.answer(f"✅ Пользователь {editor.nameRU} добавлен в редакторы!")
    else:
        await callback.message.answer(f"❌ Не удалось добавить {editor.nameRU}")

    await callback.answer()