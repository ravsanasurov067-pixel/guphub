from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import psycopg2
import asyncio
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

MINI_APP_URL = "https://bot.gaphub.uz"


def save_user_to_db(user: types.User):
    cursor.execute("""
        INSERT INTO users (
            telegram_id,
            username,
            first_name,
            last_name,
            language_code,
            is_premium
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            language_code = EXCLUDED.language_code,
            is_premium = EXCLUDED.is_premium,
            updated_at = CURRENT_TIMESTAMP
    """, (
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        user.language_code,
        user.is_premium if user.is_premium is not None else False
    ))
    conn.commit()


@dp.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    save_user_to_db(user)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть gaphub",
                    web_app=WebAppInfo(url=MINI_APP_URL)
                )
            ]
        ]
    )

    await message.answer("Запусти приложение:", reply_markup=keyboard)


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        cursor.close()
        conn.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())