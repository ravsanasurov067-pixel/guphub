from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

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

class OtabekChatRequest(BaseModel):
    message: str
    course: str = "smm"
    lesson: int = 1
    lang: str = "ru"

class ProgressCompleteRequest(BaseModel):
    telegram_id: int
    course_slug: str
    lesson_id: int

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

@app.post("/otabek/chat")
def otabek_chat(data: OtabekChatRequest):
    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    lang_name = "русском" if data.lang == "ru" else "узбекском"

    system_prompt = f"""
Ты Отабек, AI-помощник образовательной платформы gaphub.

Твоя задача: помогать ученику проходить уроки по digital-направлениям: SMM, таргет, AI и смежные темы.

Сейчас ученик находится в курсе: {data.course}.
Номер урока: {data.lesson}.
Язык ответа: отвечай на {lang_name} языке.

Правила:
1. Отвечай просто, понятно и по делу.
2. Не используй канцелярит и шаблонные фразы.
3. Если вопрос связан с темой курса, маркетингом, digital, контентом, аудиторией, продажами, продвижением или обучением, отвечай нормально.
4. Если вопрос совсем не относится к обучению, мягко верни ученика к уроку.
5. Не уходи в разговоры про знаменитостей, политику, новости, личную жизнь и случайные темы.
6. Не матерись.
7. Не говори, что ты ChatGPT.
8. Не придумывай факты, если не уверен.
9. Ответ должен быть коротким, но полезным.
10. Если ученик просит пример, дай простой пример из бизнеса, SMM или личного бренда.

Контекст урока:
Первый урок SMM объясняет, что такое SMM, зачем нужен контент, что такое целевая аудитория, как через внимание, интерес и доверие человек приходит к действию.
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": data.message
                }
            ],
            max_output_tokens=350
        )

        return {
            "answer": response.output_text
        }

    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500,
            detail="Otabek AI error"
        )
    
@app.post("/progress/complete")
def complete_lesson(data: ProgressCompleteRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO lesson_progress (
            telegram_id,
            course_slug,
            lesson_id
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (telegram_id, course_slug, lesson_id)
        DO UPDATE SET completed_at = NOW()
    """, (
        data.telegram_id,
        data.course_slug,
        data.lesson_id
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "success": True,
        "telegram_id": data.telegram_id,
        "course_slug": data.course_slug,
        "lesson_id": data.lesson_id
    }    