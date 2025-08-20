from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3, random

app = Flask(__name__)

DB_FILE = "translations.db"
TABLE_NAME = "sentences"

# --- DB Utility ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_progress():
    conn = get_db_connection()
    total = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    done = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE student_validated = 'yes'").fetchone()[0]
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
    rows = conn.execute(f"SELECT * FROM {TABLE_NAME} WHERE student_validated IS NULL OR student_validated = ''").fetchall()
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
    conn.execute(f"""
        UPDATE {TABLE_NAME}
        SET Translation=?, student_validated=?, confidence=?, reason=?
        WHERE id=?
    """, (translation, student_validated, confidence, reason, row_id))
    conn.commit()
    conn.close()
    return redirect(url_for("translate"))

if __name__ == "__main__":
    # Run on LAN (use host='0.0.0.0')
    app.run(debug=True, host="0.0.0.0", port=5000)
