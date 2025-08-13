import sqlite3
import os

def add_is_deleted_column(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Check if column exists
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cur.fetchall()]
    if 'is_deleted' not in columns:
        print(f"Adding 'is_deleted' column to {table_name}...")
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
        conn.commit()
    else:
        print(f"'is_deleted' column already exists in {table_name}.")
    conn.close()

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), '../app/data/quincaillerie.db')
    db_path = os.path.abspath(db_path)
    for table in ['sales', 'expenses']:
        add_is_deleted_column(db_path, table)
    print("Migration complete.")
