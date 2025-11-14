import asyncio
import logging
import os

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, Command
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import OpenAppButton

logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.getenv("MAX_BOT_TOKEN"))
dp = Dispatcher()

MINI_APP_URL = os.getenv("MINI_APP_URL", "").rstrip('/')
MAX_BOT_NAME = os.getenv("MAX_BOT_NAME")

@dp.message_created(Command('start'))
async def start_handler(event: MessageCreated):
    if not MAX_BOT_NAME:
        await event.message.answer("⚠️ Критическая ошибка: имя бота не настроено в конфигурации сервера.")
        return

    app_url = f"https://max.ru/{MAX_BOT_NAME}?startapp=" 

    builder = InlineKeyboardBuilder()
    builder.row(
        OpenAppButton(text="🚀 Открыть NNAImark", web_app=app_url)
    )

    await event.message.answer(
        text="Привет! Я - NNAImark, Ваш персональный навигатор в достижении целей.\n\nНажмите кнопку ниже, чтобы начать.",
        attachments=[builder.as_markup()]
    )

async def main():
    if not os.getenv("MAX_BOT_TOKEN") or not MINI_APP_URL or not MAX_BOT_NAME:
        logging.critical("Критическая ошибка: MAX_BOT_TOKEN, MINI_APP_URL или MAX_BOT_NAME не найдены. Бот не будет запущен.")
        return
    logging.info(f"Запуск бота... Имя бота: {MAX_BOT_NAME}, URL приложения: {MINI_APP_URL}")
    await bot.delete_webhook()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())