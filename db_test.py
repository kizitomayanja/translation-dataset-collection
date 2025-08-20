import sqlite3
import pandas as pd

DB_FILE = "translations.db"
TABLE_NAME = "sentences"

# Connect
conn = sqlite3.connect(DB_FILE)

# Load first 10 rows into pandas DataFrame
df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME} LIMIT 10;", conn)

print(df)

conn.close()
