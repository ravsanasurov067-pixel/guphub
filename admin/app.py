from dotenv import load_dotenv
import os

load_dotenv()
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_LOGIN = os.getenv("ADMIN_LOGIN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


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

    users = []
    user_courses = []

    if telegram_id:
        users.append({
            "telegram_id": telegram_id,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+998000000000",
            "created_at": "2026"
        })

        user_courses = ["smm", "target"]

    return render_template(
        "dashboard.html",
        users=users,
        message=message,
        user_courses=user_courses
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
    course = request.form.get("course")

    message = f"Курс {course} выдан пользователю {telegram_id}"

    return redirect(f"/dashboard?telegram_id={telegram_id}&message={message}")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8010)