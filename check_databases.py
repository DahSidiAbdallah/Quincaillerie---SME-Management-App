import sqlite3
import os

# Check database in data directory
try:
    data_db_path = 'app/data/quincaillerie.db'
    if os.path.exists(data_db_path):
        conn = sqlite3.connect(data_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in {data_db_path}:")
        if tables:
            for table in tables:
                # Count rows in each table
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  - {table[0]}: {count} rows")
        else:
            print("  No tables found")
        conn.close()
    else:
        print(f"{data_db_path} does not exist")
except Exception as e:
    print(f"Error with {data_db_path}: {e}")

# Check database in db directory
try:
    db_db_path = 'app/db/quincaillerie.db'
    if os.path.exists(db_db_path):
        conn = sqlite3.connect(db_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nTables in {db_db_path}:")
        if tables:
            for table in tables:
                # Count rows in each table
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  - {table[0]}: {count} rows")
        else:
            print("  No tables found")
        conn.close()
    else:
        print(f"{db_db_path} does not exist")
except Exception as e:
    print(f"Error with {db_db_path}: {e}")
