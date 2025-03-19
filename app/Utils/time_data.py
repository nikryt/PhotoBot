import asyncio
import time
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

# Конфигурация таймаута
TIMEOUT_SECONDS_300 = 300  # 5 минут
TIMEOUT_SECONDS_30 = 30  # 30 секунд
COUNTDOWN_STEP_10 = 10  # Шаг отсчёта в секундах
COUNTDOWN_STEP_5 = 5  # Шаг отсчёта в секундах


async def schedule_countdown(
        message: Message,
        bot: Bot,
        state: FSMContext,
        timeout: int = TIMEOUT_SECONDS_30
):
    """Запускает таймер обратного отсчёта для меню"""
    data = await state.get_data()

    # Отменяем предыдущий таймер если есть
    if 'countdown_task' in data:
        data['countdown_task'].cancel()

    # Создаем новую задачу отсчёта
    countdown_task = asyncio.create_task(
        _countdown_handler(message, bot, state, timeout)
    )

    # Сохраняем задачу в состоянии
    await state.update_data(
        countdown_task=countdown_task,
        last_activity=time.time()
    )


async def _countdown_handler(
        message: Message,
        bot: Bot,
        state: FSMContext,
        timeout: int
):
    """Обработчик обратного отсчёта"""
    try:
        remaining = timeout
        warning_sent = False
        countdown_msg = None

        while remaining > 0:
            await asyncio.sleep(COUNTDOWN_STEP_5)
            remaining -= COUNTDOWN_STEP_5

            # Проверяем активность пользователя
            data = await state.get_data()
            if data.get('last_activity', 0) > time.time() - COUNTDOWN_STEP_5:
                remaining = timeout  # Сброс таймера при активности
                warning_sent = False
                if countdown_msg:
                    await countdown_msg.delete()
                continue

            # Показываем/обновляем предупреждение
            if remaining <= 60 and not warning_sent:
                countdown_msg = await bot.send_message(
                    message.chat.id,
                    f"⚠️ Сессия закроется через {remaining} сек."
                )
                warning_sent = True
            elif warning_sent:
                try:
                    await countdown_msg.edit_text(
                        f"⚠️ Сессия закроется через {remaining} сек."
                    )
                except:
                    pass

        # Таймаут истек
        await bot.send_message(
            message.chat.id,
            "🚫 Время сессии истекло. Выполнен выход из меню."
        )
        await state.clear()

    except asyncio.CancelledError:
        # Таймер был отменен новым действием
        if countdown_msg:
            await countdown_msg.delete()
    finally:
        await state.update_data(countdown_task=None)