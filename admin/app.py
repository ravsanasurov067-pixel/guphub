from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_LOGIN = os.getenv("ADMIN_LOGIN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

cursor = conn.cursor()


def get_user(telegram_id):
    cursor.execute("""
        SELECT telegram_id, username, first_name, last_name, phone, created_at
        FROM users
        WHERE telegram_id = %s
    """, (telegram_id,))

    result = cursor.fetchone()

    if result:
        return {
            "telegram_id": result[0],
            "username": result[1],
            "first_name": result[2],
            "last_name": result[3],
            "phone": result[4],
            "created_at": result[5]
        }

    return None


def get_user_courses(telegram_id):
    cursor.execute("""
        SELECT c.slug
        FROM user_courses uc
        JOIN courses c ON uc.course_id = c.id
        WHERE uc.telegram_id = %s
    """, (telegram_id,))

    return [row[0] for row in cursor.fetchall()]

def get_all_users():
    cursor.execute("""
        SELECT telegram_id, username, first_name, last_name, phone, created_at
        FROM users
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    users = []
    for row in rows:
        users.append({
            "telegram_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "phone": row[4],
            "created_at": row[5]
        })

    return users

def remove_user_course(telegram_id, course_slug):
    cursor.execute("SELECT id FROM courses WHERE slug = %s", (course_slug,))
    course = cursor.fetchone()

    if course:
        course_id = course[0]

        cursor.execute("""
            DELETE FROM user_courses
            WHERE telegram_id = %s AND course_id = %s
        """, (telegram_id, course_id))

        conn.commit()

def remove_user_course(telegram_id, course_slug):
    cursor.execute("SELECT id FROM courses WHERE slug = %s", (course_slug,))
    course = cursor.fetchone()

    if course:
        course_id = course[0]

        cursor.execute("""
            DELETE FROM user_courses
            WHERE telegram_id = %s AND course_id = %s
        """, (telegram_id, course_id))

        conn.commit()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login = request.form.get("login")
        password = request.form.get("password")

        if login == ADMIN_LOGIN and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")

    telegram_id = request.args.get("telegram_id")
    message = request.args.get("message")

    users = get_all_users()
    
    for user in users:
        user["courses"] = get_user_courses(user["telegram_id"])
    user_courses = []

    if telegram_id:
        user_courses = get_user_courses(telegram_id)

    return render_template(
        "dashboard.html",
        users=users,
        message=message,
        user_courses=user_courses,
        selected_telegram_id=telegram_id
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/give-access", methods=["POST"])
def give_access():
    if not session.get("admin"):
        return redirect("/")

    telegram_id = request.form.get("telegram_id")
    course_slug = request.form.get("course")

    cursor.execute("SELECT id FROM courses WHERE slug = %s", (course_slug,))
    course = cursor.fetchone()

    if course:
        course_id = course[0]

        cursor.execute("""
            INSERT INTO user_courses (telegram_id, course_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (telegram_id, course_id))

        conn.commit()
        message = f"Курс {course_slug} выдан пользователю {telegram_id}"
    else:
        message = "Курс не найден"

    return redirect(f"/dashboard?telegram_id={telegram_id}&message={message}")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8010)

@app.route("/remove-access", methods=["POST"])
def remove_access():
    if not session.get("admin"):
        return redirect("/")

    telegram_id = request.form.get("telegram_id")
    course_slug = request.form.get("course")

    remove_user_course(telegram_id, course_slug)

    message = f"Курс {course_slug} удален у пользователя {telegram_id}"
    return redirect(f"/dashboard?telegram_id={telegram_id}&message={message}")