from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

# Токен от BotFather
TOKEN = "8729696270:AAGCFeBvkFOir3qfqHAg4XZ82kgJkMvCSs4"

# Создаём объекты бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Локальный URL Mini App (пока пустой)
MINI_APP_URL = "https://pre-yukon-asking-cats.trycloudflare.com"

@dp.message(Command("start"))
async def start(message: types.Message):

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="Открыть gaphub",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )]
        ],
        resize_keyboard=True
    )

    await message.answer("Запусти приложение:", reply_markup=keyboard)

async def main():
    try:
        # Старт polling в aiogram 3.26.0
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())