from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from dotenv import load_dotenv
import bcrypt
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user and bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8")
        ):
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        return "Invalid Username or Password"

    return render_template("login.html")


@app.route("/add-employee", methods=["GET", "POST"])
def add_employee():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        employee_code = request.form["employee_code"]
        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        department_id = request.form["department_id"] or None
        designation = request.form["designation"]
        joining_date = request.form["joining_date"] or None

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO employees
            (
                employee_code,
                full_name,
                email,
                phone,
                department_id,
                designation,
                joining_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            employee_code,
            full_name,
            email,
            phone,
            department_id,
            designation,
            joining_date
        ))

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("dashboard"))

    return render_template("add_employee.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM employees")
    total_employees = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM employees WHERE status = 'Active'"
    )
    active_employees = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM documents WHERE verification_status = 'Pending'"
    )
    pending_documents = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM leave_requests WHERE status = 'Pending'"
    )
    pending_leaves = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return render_template(
        "dashboard.html",
        total_employees=total_employees,
        active_employees=active_employees,
        pending_documents=pending_documents,
        pending_leaves=pending_leaves
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)