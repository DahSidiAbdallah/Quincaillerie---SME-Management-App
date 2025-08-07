#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, './app')
from data.database import DatabaseManager

def check_tables():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("All tables:", [t[0] for t in tables])
    
    # Check sales table structure
    cursor.execute("PRAGMA table_info(sales)")
    sales_info = cursor.fetchall()
    print("\nSales table structure:")
    for col in sales_info:
        print(f"  {col[1]} - {col[2]}")
    
    # Check if we have sales data
    cursor.execute("SELECT COUNT(*) FROM sales")
    sales_count = cursor.fetchone()[0]
    print(f"\nSales records: {sales_count}")
    
    # Check sale dates
    cursor.execute("SELECT sale_date FROM sales LIMIT 5")
    dates = cursor.fetchall()
    print("Sales dates:", [d[0] for d in dates])
    
    conn.close()

if __name__ == "__main__":
    check_tables()
