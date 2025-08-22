from flask import Flask, render_template, request, redirect, url_for, jsonify
import psycopg2
import psycopg2.extras
import random

app = Flask(__name__)

DB_PARAMS = {
    "dbname": "translations",
    "user": "kmayanja",
    "password": "kmayanja",
    "host": "localhost",
    "port": "5432"
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
    return render_template("index.html", done=done, total=total, percent=percent)

@app.route("/translate")
def translate():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE student_validated IS NULL OR student_validated = ''")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        return render_template("finished.html")
    row = random.choice(rows)
    return render_template("translate.html", sentence=row, table=TABLE_NAME)

@app.route("/submit", methods=["POST"])
def submit():
    row_id = request.form["id"]
    translation = request.form["translation"]
    student_validated = request.form["student_validated"]
    confidence = request.form["confidence"]
    reason = request.form["reason"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE {TABLE_NAME}
        SET translation=%s, student_validated=%s, confidence=%s, reason=%s
        WHERE id=%s
    """, (translation, student_validated, confidence, reason, row_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("translate"))

# app.add_url_rule(
#     "/favicon.ico",
#     endpoint="favicon",
#     redirect_to=url_for("static", filename="favicon.ico"),
# )

if __name__ == "__main__":
    # Run on LAN (use host='0.0.0.0')
    app.run(debug=True, host="0.0.0.0", port=5000)