#!/usr/bin/env python3
# Quick database debug script

from data.database import DatabaseManager
import sqlite3

def main():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    # Check sales table structure
    print('=== SALES TABLE STRUCTURE ===')
    cursor.execute('PRAGMA table_info(sales)')
    columns = cursor.fetchall()
    for col in columns:
        print(f'  {col[1]} ({col[2]})')

    print()

    # Check if expenses table exists
    print('=== EXPENSES TABLE CHECK ===')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'")
    result = cursor.fetchone()
    if result:
        print('Expenses table exists')
        cursor.execute('PRAGMA table_info(expenses)')
        columns = cursor.fetchall()
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
    else:
        print('Expenses table DOES NOT EXIST!')

    print()

    # Sample sales data
    print('=== SAMPLE SALES DATA ===')
    cursor.execute('SELECT * FROM sales LIMIT 2')
    sales = cursor.fetchall()
    for sale in sales:
        print(f'  {dict(sale)}')

    print()

    # Check all sales amounts
    print('=== ALL SALES AMOUNTS ===')
    cursor.execute('SELECT total_amount, sale_date FROM sales')
    all_sales = cursor.fetchall()
    for sale in all_sales:
        print(f'  Amount: {sale[0]}, Date: {sale[1]}')

    conn.close()

if __name__ == '__main__':
    main()
