from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    WebAppInfo,
)
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


def get_user_phone(telegram_id: int):
    cursor.execute("""
        SELECT phone
        FROM users
        WHERE telegram_id = %s
    """, (telegram_id,))
    result = cursor.fetchone()
    return result[0] if result and result[0] else None


def save_phone_to_db(telegram_id: int, phone: str):
    cursor.execute("""
        UPDATE users
        SET phone = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = %s
    """, (phone, telegram_id))
    conn.commit()


def get_open_app_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть gaphub",
                    web_app=WebAppInfo(url=MINI_APP_URL)
                )
            ]
        ]
    )


def get_contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Поделиться номером", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


@dp.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    save_user_to_db(user)

    phone = get_user_phone(user.id)

    if phone:
        await message.answer(
            "Добро пожаловать. Можешь открыть gaphub:",
            reply_markup=ReplyKeyboardRemove()
        )

        await message.answer(
            "Открыть приложение:",
            reply_markup=get_open_app_keyboard()
        )
    else:
        await message.answer(
            "Сначала отправь свой номер:",
            reply_markup=get_contact_keyboard()
        )


@dp.message(lambda message: message.contact is not None)
async def handle_contact(message: types.Message):
    contact = message.contact

    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer("Отправь, пожалуйста, свой номер.")
        return

    phone = contact.phone_number
    if not phone.startswith("+"):
     phone = "+" + phone
    user_id = message.from_user.id

    save_phone_to_db(user_id, phone)

    await message.answer(
        "Номер сохранен. Теперь можешь открыть gaphub:",
        reply_markup=ReplyKeyboardRemove()
    )

    await message.answer(
        "Открыть приложение:",
        reply_markup=get_open_app_keyboard()
    )


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        cursor.close()
        conn.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())