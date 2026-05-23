from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "visitor_secret_key"


def init_db():
    conn = sqlite3.connect("visitors.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_number TEXT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            service_type TEXT,
            appointment_type TEXT,
            reason TEXT,
            consultant TEXT,
            status TEXT,
            checkin_time TEXT
        )
    """)

    conn.commit()
    conn.close()


def generate_token():
    conn = sqlite3.connect("visitors.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM visitors")
    count = c.fetchone()[0] + 1
    conn.close()
    return f"TKN-{count:03d}"


@app.route("/")
def home():
    if "admin" not in session:
        return redirect("/login")
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    if "admin" not in session:
        return redirect("/login")

    token_number = generate_token()
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    service_type = request.form["service_type"]
    appointment_type = request.form["appointment_type"]
    reason = request.form["reason"]
    consultant = request.form["consultant"]
    status = "Waiting"
    checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("visitors.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO visitors
        (token_number, name, email, phone, service_type, appointment_type, reason, consultant, status, checkin_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        token_number, name, email, phone, service_type,
        appointment_type, reason, consultant, status, checkin_time
    ))

    conn.commit()
    conn.close()

    return redirect("/admin")
@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    search = request.args.get("search", "").strip()

    conn = sqlite3.connect("visitors.db")
    c = conn.cursor()

    if search:

        like = f"%{search}%"

        c.execute("""
            SELECT * FROM visitors

            WHERE
                token_number LIKE ?
                OR name LIKE ?
                OR email LIKE ?
                OR phone LIKE ?
                OR service_type LIKE ?
                OR appointment_type LIKE ?
                OR reason LIKE ?
                OR consultant LIKE ?
                OR status LIKE ?

            ORDER BY id DESC
        """, (
            like,
            like,
            like,
            like,
            like,
            like,
            like,
            like,
            like
        ))

    else:

        c.execute("""
            SELECT * FROM visitors
            ORDER BY id DESC
        """)

    visitors = c.fetchall()

    # TOTAL VISITORS
    c.execute("SELECT COUNT(*) FROM visitors")
    total_visitors = c.fetchone()[0]

    # TODAY VISITORS
    today = datetime.now().strftime("%Y-%m-%d")

    c.execute("""
        SELECT COUNT(*)
        FROM visitors
        WHERE checkin_time LIKE ?
    """, (f"{today}%",))

    today_visitors = c.fetchone()[0]

    # WAITING VISITORS
    c.execute("""
        SELECT COUNT(*)
        FROM visitors
        WHERE status = 'Waiting'
    """)

    waiting_visitors = c.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        visitors=visitors,
        search=search,
        total_visitors=total_visitors,
        today_visitors=today_visitors,
        waiting_visitors=waiting_visitors
    )

@app.route("/update-status/<int:id>/<status>")
def update_status(id, status):
    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("visitors.db")
    c = conn.cursor()
    c.execute("UPDATE visitors SET status = ? WHERE id = ?", (status, id))
    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/delete/<int:id>")
def delete_visitor(id):
    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("visitors.db")
    c = conn.cursor()
    c.execute("DELETE FROM visitors WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/")

        return "Invalid username or password"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)