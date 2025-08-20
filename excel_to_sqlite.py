import sqlite3
import pandas as pd
import os

# --- CONFIG ---
data_folder = "data"              # folder containing Excel files
sqlite_file = "translations.db"   # output SQLite database
table_name = "sentences"          # target table
# --------------

# Make sure folder exists
if not os.path.exists(data_folder):
    raise FileNotFoundError(f"❌ Folder '{data_folder}' not found. Please create it and add Excel files.")

# Collect Excel files
excel_files = [f for f in os.listdir(data_folder) if f.endswith((".xlsx", ".xls"))]

if not excel_files:
    raise FileNotFoundError(f"❌ No Excel files found in '{data_folder}'")

print(f"📂 Found {len(excel_files)} Excel files in '{data_folder}'")

# Required columns
required_cols = ["humanized_text", "translation", "student_validated", "confidence", "reason"]

# Create / overwrite SQLite DB
conn = sqlite3.connect(sqlite_file)
all_dataframes = []

for file in excel_files:
    file_path = os.path.join(data_folder, file)
    print(f"🔄 Processing {file_path}...")

    try:
        # Load Excel file (only first sheet for simplicity, can loop if needed)
        df = pd.read_excel(file_path)

        # Add missing required columns
        for col in required_cols:
            if col not in df.columns:
                df[col] = None  # add empty column

        # Keep only the required columns (in consistent order)
        df = df[required_cols]

        # Add file identifier column
        df["SourceFile"] = file

        all_dataframes.append(df)

    except Exception as e:
        print(f"⚠️ Skipping {file_path} due to error: {e}")

# Combine all into one big DataFrame
if not all_dataframes:
    raise RuntimeError("❌ No valid Excel files processed.")

final_df = pd.concat(all_dataframes, ignore_index=True)

# Save into SQLite
final_df.to_sql(table_name, conn, if_exists="replace", index=True, index_label="id")

conn.close()
print(f"✅ All Excel files saved into '{sqlite_file}' with table '{table_name}'")
