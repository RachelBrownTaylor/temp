import json
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    Response,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
DATABASE_PATH = os.environ.get("DB_PATH", "app.db")


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'admin'))
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY,
            numbering_temp INTEGER NOT NULL,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            choices TEXT NOT NULL,
            answer INTEGER NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_choice INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(user_id, question_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(question_id) REFERENCES questions(id)
        )
        """
    )
    db.commit()


@app.before_request
def before_request():
    init_db()


def create_default_admin():
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    if not username or not password:
        return
    db = get_db()
    cur = db.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cur.fetchone() is None:
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), "admin"),
        )
        db.commit()
def create_default_user():
    username = os.environ.get("DEFAULT_USER_USERNAME")
    password = os.environ.get("DEFAULT_USER_PASSWORD")
    if not username or not password:
        return
    db = get_db()
    cur = db.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cur.fetchone() is None:
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')",
            (username, generate_password_hash(password)),
        )
        db.commit()


with app.app_context():
    create_default_admin()
    create_default_user()


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            user_id = session.get("user_id")
            if user_id is None:
                return redirect(url_for("login"))
            if role is not None and session.get("role") != role:
                abort(403)
            return view(**kwargs)

        return wrapped_view

    return decorator


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        cur = db.execute(
            "SELECT id, password_hash, role FROM users WHERE username = ?",
            (username,),
        )
        user = cur.fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = username
            session["role"] = user["role"]
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("question", numbering=1))
        flash("로그인에 실패했습니다. 다시 확인하세요.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def get_question_by_number(numbering):
    db = get_db()
    cur = db.execute(
        "SELECT * FROM questions WHERE numbering_temp = ? ORDER BY numbering_temp",
        (numbering,),
    )
    return cur.fetchone()


def get_questions():
    db = get_db()
    cur = db.execute("SELECT * FROM questions ORDER BY numbering_temp")
    return cur.fetchall()


@app.route("/")
def index():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    if session.get("user_id"):
        return redirect(url_for("question", numbering=1))
    return redirect(url_for("login"))


@app.route("/questions/<int:numbering>", methods=["GET", "POST"])
@login_required(role="user")
def question(numbering):
    q = get_question_by_number(numbering)
    if q is None:
        flash("해당 문항이 없습니다.")
        return redirect(url_for("question", numbering=1))

    db = get_db()
    user_id = session["user_id"]
    if request.method == "POST":
        choice = request.form.get("choice")
        if choice is not None:
            timestamp = datetime.utcnow().isoformat()
            db.execute(
                "INSERT INTO responses (user_id, question_id, selected_choice, timestamp)"
                " VALUES (?, ?, ?, ?)"
                " ON CONFLICT(user_id, question_id) DO UPDATE SET selected_choice=excluded.selected_choice, timestamp=excluded.timestamp",
                (user_id, q["id"], int(choice), timestamp),
            )
            db.commit()
            flash("답안이 저장되었습니다.")
        action = request.form.get("action")
        next_number = numbering
        if action == "next":
            next_number = numbering + 1
        elif action == "prev":
            next_number = numbering - 1
        elif action == "stay":
            next_number = numbering

        questions = get_questions()
        numbers = [item["numbering_temp"] for item in questions]
        if next_number not in numbers:
            if action == "next" and numbers:
                next_number = numbers[-1]
            elif action == "prev" and numbers:
                next_number = numbers[0]
            else:
                next_number = numbering
        return redirect(url_for("question", numbering=next_number))

    cur = db.execute(
        "SELECT selected_choice FROM responses WHERE user_id = ? AND question_id = ?",
        (user_id, q["id"]),
    )
    existing = cur.fetchone()
    selected_choice = existing["selected_choice"] if existing else None

    questions = get_questions()
    progress = []
    for item in questions:
        cur = db.execute(
            "SELECT 1 FROM responses WHERE user_id = ? AND question_id = ?",
            (user_id, item["id"]),
        )
        progress.append(
            {
                "number": item["numbering_temp"],
                "answered": cur.fetchone() is not None,
            }
        )

    choices = json.loads(q["choices"])
    return render_template(
        "question.html",
        question=q,
        choices=choices,
        selected_choice=selected_choice,
        progress=progress,
    )


@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    db = get_db()
    questions = get_questions()
    users = db.execute("SELECT id, username FROM users WHERE role = 'user'").fetchall()

    results = []
    for user in users:
        for q in questions:
            response = db.execute(
                "SELECT selected_choice, timestamp FROM responses WHERE user_id = ? AND question_id = ?",
                (user["id"], q["id"]),
            ).fetchone()
            selected = response["selected_choice"] if response else None
            timestamp = response["timestamp"] if response else None
            correct = None
            if selected is not None:
                correct = int(selected) == int(q["answer"])
            results.append(
                {
                    "user": user["username"],
                    "question_number": q["numbering_temp"],
                    "question_id": q["id"],
                    "topic": q["topic"],
                    "question": q["question"],
                    "selected": selected,
                    "answer": q["answer"],
                    "correct": correct,
                    "timestamp": timestamp,
                }
            )

    per_question = []
    for q in questions:
        answered = db.execute(
            "SELECT COUNT(*) FROM responses WHERE question_id = ?",
            (q["id"],),
        ).fetchone()[0]
        correct_count = db.execute(
            "SELECT COUNT(*) FROM responses WHERE question_id = ? AND selected_choice = ?",
            (q["id"], q["answer"]),
        ).fetchone()[0]
        accuracy = (correct_count / answered * 100) if answered else None
        per_question.append(
            {
                "question_number": q["numbering_temp"],
                "answered": answered,
                "correct": correct_count,
                "accuracy": accuracy,
            }
        )

    return render_template(
        "admin_dashboard.html",
        results=results,
        per_question=per_question,
    )


def validate_dataset(data):
    if not isinstance(data, list):
        return False
    required_keys = {"numbering_temp", "id", "topic", "question", "choices", "answer"}
    for item in data:
        if not isinstance(item, dict):
            return False
        if not required_keys.issubset(item.keys()):
            return False
        if not isinstance(item["choices"], list):
            return False
        if not isinstance(item["answer"], int):
            return False
    return True


@app.route("/admin/load", methods=["GET", "POST"])
@login_required(role="admin")
def load_dataset():
    if request.method == "POST":
        path = request.form.get("path", "").strip()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            flash("파일을 읽을 수 없거나 형식이 잘못되었습니다.")
            return render_template("load_dataset.html")
        if not validate_dataset(data):
            flash("데이터 구조가 올바르지 않습니다.")
            return render_template("load_dataset.html")

        db = get_db()
        db.execute("DELETE FROM responses")
        db.execute("DELETE FROM questions")
        for item in data:
            db.execute(
                "INSERT INTO questions (id, numbering_temp, topic, question, choices, answer)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["numbering_temp"],
                    item["topic"],
                    item["question"],
                    json.dumps(item["choices"], ensure_ascii=False),
                    item["answer"],
                ),
            )
        db.commit()
        flash("문제가 성공적으로 로드되었습니다.")
        return redirect(url_for("admin_dashboard"))
    return render_template("load_dataset.html")


@app.route("/admin/export")
@login_required(role="admin")
def export_results():
    export_format = request.args.get("format", "csv")
    db = get_db()
    query = db.execute(
        """
        SELECT q.id AS question_id, q.topic, q.question, r.user_id, u.username,
               r.selected_choice, q.answer,
               CASE WHEN r.selected_choice = q.answer THEN 1 ELSE 0 END AS correct,
               r.timestamp
        FROM responses r
        JOIN questions q ON r.question_id = q.id
        JOIN users u ON r.user_id = u.id
        ORDER BY r.timestamp
        """
    ).fetchall()

    rows = [dict(row) for row in query]
    if export_format == "json":
        data = json.dumps(rows, ensure_ascii=False)
        return Response(
            data,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=results.json"},
        )

    # CSV export
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "question_id",
            "topic",
            "question",
            "user_id",
            "username",
            "selected_choice",
            "correct_answer",
            "is_correct",
            "timestamp",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row["question_id"],
                row["topic"],
                row["question"],
                row["user_id"],
                row["username"],
                row["selected_choice"],
                row["answer"],
                row["correct"],
                row["timestamp"],
            ]
        )
    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=results.csv"},
    )


def load_initial_dataset():
    dataset_path = os.environ.get("DATASET_PATH")
    if not dataset_path:
        return
    db = get_db()
    cur = db.execute("SELECT COUNT(*) FROM questions")
    if cur.fetchone()[0] > 0:
        return
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    if not validate_dataset(data):
        return
    for item in data:
        db.execute(
            "INSERT INTO questions (id, numbering_temp, topic, question, choices, answer)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                item["id"],
                item["numbering_temp"],
                item["topic"],
                item["question"],
                json.dumps(item["choices"], ensure_ascii=False),
                item["answer"],
            ),
        )
    db.commit()


load_initial_dataset()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
