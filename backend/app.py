from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bot.gaphub.uz",
        "https://admin.gaphub.uz",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


@app.get("/user/{telegram_id}")
def get_user(telegram_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT phone
        FROM users
        WHERE telegram_id = %s
    """, (telegram_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return {"phone": result[0]}

    return {"phone": None}


@app.get("/mycourses/{telegram_id}")
def get_my_courses(telegram_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.slug,
            c.title
        FROM user_courses uc
        JOIN courses c ON uc.course_id = c.id
        WHERE uc.telegram_id = %s
          AND c.is_active = TRUE
        ORDER BY c.id
    """, (telegram_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    courses = []

    for row in rows:
        courses.append({
            "slug": row[0],
            "title": row[1],
            "lessons_count": 0,
            "progress": 0
        })

    return {
        "telegram_id": telegram_id,
        "courses": courses
    }