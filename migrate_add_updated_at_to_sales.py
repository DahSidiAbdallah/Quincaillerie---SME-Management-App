"""
Migration script to add 'updated_at' column to 'sales' table if it does not exist.
Run this script once with your Python environment activated.
"""
import sqlite3
import os

# Path to your SQLite database (corrected to app/data/quincaillerie.db)
DB_PATH = os.path.join(os.path.dirname(__file__), 'app', 'data', 'quincaillerie.db')


ALTER_SQL = "ALTER TABLE sales ADD COLUMN updated_at TIMESTAMP;"
UPDATE_SQL = "UPDATE sales SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;"

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not column_exists(cursor, 'sales', 'updated_at'):
        try:
            cursor.execute(ALTER_SQL)
            conn.commit()
            print("Column 'updated_at' added to 'sales' table.")
        except Exception as e:
            print(f"Error adding column: {e}")
    else:
        print("Column 'updated_at' already exists.")

    # Set CURRENT_TIMESTAMP for existing rows where updated_at is NULL
    try:
        cursor.execute(UPDATE_SQL)
        conn.commit()
        print("Set CURRENT_TIMESTAMP for existing rows.")
    except Exception as e:
        print(f"Error updating existing rows: {e}")
    conn.close()

if __name__ == "__main__":
    main()
