import sqlite3
import psycopg2
from psycopg2 import sql

# Connect to SQLite
try:
    sqlite_conn = sqlite3.connect('translations.db')
    sqlite_cursor = sqlite_conn.cursor()
except Exception as e:
    raise ConnectionError(f"❌ Failed to connect to SQLite: {e}")

# Connect to PostgreSQL
try:
    pg_conn = psycopg2.connect(
        dbname="translations",
        user="kmayanja",
        # password="kmayanja",
        host="localhost",
        port="5432"
    )
    pg_cursor = pg_conn.cursor()
except Exception as e:
    raise ConnectionError(f"❌ Failed to connect to PostgreSQL: {e}")

# Step 1: Get SQLite table schema
sqlite_cursor.execute("PRAGMA table_info(sentences)")
columns = sqlite_cursor.fetchall()
if not columns:
    raise RuntimeError("❌ Table 'sentences' does not exist in SQLite database.")

# Step 2: Drop existing PostgreSQL table (if needed) and create new one
try:
    pg_cursor.execute("DROP TABLE IF EXISTS sentences")
    pg_conn.commit()
except Exception as e:
    pg_conn.rollback()
    raise RuntimeError(f"❌ Failed to drop existing table: {e}")

# Explicitly define table schema to match SQLite (with student_validated as TEXT)
create_table_query = """
CREATE TABLE sentences (
    id SERIAL PRIMARY KEY,
    humanized_text TEXT,
    translation TEXT,
    student_validated TEXT,  -- Changed to TEXT to handle values like "hold"
    confidence FLOAT,
    reason TEXT,
    "SourceFile" VARCHAR(255)
);
"""
try:
    pg_cursor.execute(create_table_query)
    pg_conn.commit()
    print("✅ Created 'sentences' table in PostgreSQL")
except Exception as e:
    pg_conn.rollback()
    raise RuntimeError(f"❌ Failed to create table in PostgreSQL: {e}")

# Step 3: Copy data from SQLite to PostgreSQL
sqlite_cursor.execute("SELECT id, humanized_text, translation, student_validated, confidence, reason, SourceFile FROM sentences")
rows = sqlite_cursor.fetchall()

# Define columns for INSERT
col_names = ['id', 'humanized_text', 'translation', 'student_validated', 'confidence', 'reason', 'SourceFile']
placeholders = ', '.join(['%s'] * len(col_names))
insert_query = sql.SQL('INSERT INTO sentences ({}) VALUES ({})').format(
    sql.SQL(', ').join([sql.Identifier(col) for col in col_names]),
    sql.SQL(placeholders)
)

try:
    for row in rows:
        # No boolean conversion needed since student_validated is TEXT
        pg_cursor.execute(insert_query, row)
    pg_conn.commit()
    print(f"✅ Copied {len(rows)} rows to PostgreSQL")
except Exception as e:
    pg_conn.rollback()
    raise RuntimeError(f"❌ Failed to copy data to PostgreSQL: {e}")

# Close connections
sqlite_cursor.close()
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()
print("✅ Migration completed successfully")