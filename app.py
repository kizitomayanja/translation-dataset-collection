from flask import Flask, render_template, request, redirect, url_for, jsonify
import psycopg2
import psycopg2.extras
import random
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)

# Dummy user object for template
class DummyUser:
    is_authenticated = False

current_user = DummyUser()

DB_PARAMS = {
    "dbname": os.getenv("dbname"),
    "user": os.getenv("user"),
    "password": os.getenv("password"),
    "host": os.getenv("host"),
    "port": os.getenv("port"),
}
TABLE_NAME = "sentences"

# --- DB Utility ---
def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    return conn

def get_progress():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE student_validated = 'yes'")
    done = cur.fetchone()[0]
    cur.close()
    conn.close()
    return done, total

# --- Routes ---
@app.route("/")
def index():
    done, total = get_progress()
    percent = (done / total * 100) if total else 0
    return render_template("index.html", done=done, total=total, percent=percent, current_user=current_user)

@app.route("/translate")
def translate():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    done, total = get_progress()
    percent = (done / total * 100) if total else 0
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE student_validated IS NULL OR student_validated = ''")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        return render_template("finished.html", done=done, total=total, percent=percent, current_user=current_user)
    row = random.choice(rows)
    return render_template("translate.html", sentence=row, table=TABLE_NAME, done=done, total=total, percent=percent, current_user=current_user)

@app.route("/submit", methods=["POST"])
def submit():
    row_id = request.form["id"]
    translation = request.form["translation"]
    student_validated = request.form["student_validated"]
    confidence = request.form["confidence"]
    reason = request.form["reason"]
    username = current_user.username if current_user.is_authenticated else "anonymous"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE {TABLE_NAME}
        SET translation=%s, student_validated=%s, confidence=%s, reason=%s, validated_by=%s
        WHERE id=%s
    """, (translation, student_validated, confidence, reason, username, row_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("translate"))

#ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user', ADD COLUMN translation_count INTEGER NOT NULL DEFAULT 0;
# 
# 

@app.route("/home")
def home():
    done, total = get_progress()
    percent = (done / total * 100) if total else 0
    return render_template("index.html", current_user=current_user, done=done, total=total, percent=percent)  # Adjust as needed

@app.route("/about")
def about():
    done, total = get_progress()
    percent = (done / total * 100) if total else 0
    return render_template("about.html", current_user=current_user, done=done, total=total, percent=percent)

@app.route("/contact")
def contact():
    done, total = get_progress()
    percent = (done / total * 100) if total else 0
    return render_template("contact.html", current_user=current_user, done=done, total=total, percent=percent)

@app.route("/profile")
def profile():
    done, total = get_progress()
    percent = (done / total * 100) if total else 0
    # Add authentication logic as needed
    return render_template("profile.html", current_user=current_user, done=done, total=total, percent=percent)

@app.route("/logout")
def logout():
    # Add logout logic as needed
    current_user.is_authenticated = False
    current_user.username = None
    current_user.email = None
    return redirect(url_for("signup"))

@app.route("/login")
def login():
    return render_template("login.html", current_user=current_user)

@app.route("/signup")
def signup():# Provide default progress values
    done, total = get_progress()
    percent = (done / total * 100) if total else 0
    return render_template("signup.html", current_user=current_user, done=done, total=total, percent=percent)

@app.route("/authenticate", methods=["POST"])
def authenticate():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and check_password_hash(user["password"], password):
        # User authenticated successfully
        # Implement session management as needed
        current_user.is_authenticated = True
        current_user.username = user["username"]
        current_user.email = user["email"]
        return redirect(url_for("home"))
    else:
        # Authentication failed
        return redirect(url_for("login"))

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_password))
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        return redirect(url_for("signup"))
    
    current_user.is_authenticated = True
    cur.close()
    conn.close()
    current_user.username = username
    current_user.email = email
    return redirect(url_for("home"))

@app.route("/leaderboard")
def leaderboard():
    done, total = get_progress()
    percent = (done / total * 100) if total else 0

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT username, translation_count FROM users ORDER BY translation_count DESC, username ASC")
    users = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("leaderboard.html", users=users, current_user=current_user, done=done, total=total, percent=percent)

# app.add_url_rule(
#     "/favicon.ico",
#     endpoint="favicon",
#     redirect_to=url_for("static", filename="favicon.ico"),
# )

if __name__ == "__main__":
    # Run on LAN (use host='0.0.0.0')
    app.run(debug=True, host="0.0.0.0", port=5000)