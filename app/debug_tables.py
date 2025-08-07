#!/usr/bin/env python3
# Check sale_details table

from data.database import DatabaseManager
import sqlite3

def main():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    # Check if sale_details table exists
    print('=== CHECKING SALE_DETAILS TABLE ===')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sale_details'")
    result = cursor.fetchone()
    if result:
        print('sale_details table EXISTS')
        cursor.execute('PRAGMA table_info(sale_details)')
        columns = cursor.fetchall()
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
        
        cursor.execute('SELECT COUNT(*) FROM sale_details')
        count = cursor.fetchone()[0]
        print(f'Records in sale_details: {count}')
        
        if count > 0:
            cursor.execute('SELECT * FROM sale_details LIMIT 3')
            records = cursor.fetchall()
            for record in records:
                print(f'  {dict(record)}')
    else:
        print('sale_details table DOES NOT EXIST!')
        print('This explains why top selling products is empty')

    # Check all table names
    print('\n=== ALL TABLES IN DATABASE ===')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f'  {table[0]}')

    conn.close()

if __name__ == '__main__':
    main()
