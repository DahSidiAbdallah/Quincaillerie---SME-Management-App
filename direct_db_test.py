#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Database Access Test for Quincaillerie App
"""

import os
import sys
import sqlite3
import json

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

def check_database(db_path):
    """Direct check of database tables and contents"""
    print(f"\n=== Checking Database: {db_path} ===")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file does not exist at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check products
        if 'products' in tables:
            cursor.execute("SELECT COUNT(*) as count FROM products")
            count = cursor.fetchone()['count']
            print(f"\nProducts count: {count}")
            
            if count > 0:
                cursor.execute("""
                    SELECT id, name, description, purchase_price, sale_price, 
                           current_stock, min_stock_alert, is_active
                    FROM products LIMIT 5
                """)
                print("Sample products:")
                for row in cursor.fetchall():
                    print(json.dumps(dict(row), indent=2))
        
        # Check customers
        if 'customers' in tables:
            cursor.execute("SELECT COUNT(*) as count FROM customers")
            count = cursor.fetchone()['count']
            print(f"\nCustomers count: {count}")
            
            if count > 0:
                cursor.execute("""
                    SELECT id, name, phone, email, address, is_active
                    FROM customers LIMIT 5
                """)
                print("Sample customers:")
                for row in cursor.fetchall():
                    print(json.dumps(dict(row), indent=2))
        
        # Execute the inventory stats query directly
        print("\nDirect Inventory Stats Query:")
        cursor.execute('SELECT COUNT(*) as total FROM products WHERE is_active = 1')
        total = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT COUNT(*) as in_stock FROM products
            WHERE is_active = 1 AND current_stock > 0
        ''')
        in_stock = cursor.fetchone()['in_stock']
        
        cursor.execute('''
            SELECT COUNT(*) as low_stock FROM products
            WHERE is_active = 1 AND current_stock <= min_stock_alert
        ''')
        low_stock = cursor.fetchone()['low_stock']
        
        cursor.execute('''
            SELECT COALESCE(SUM(purchase_price * current_stock), 0) as total_value
            FROM products WHERE is_active = 1
        ''')
        total_value = cursor.fetchone()['total_value']
        
        stats = {
            'total': total,
            'in_stock': in_stock,
            'low_stock': low_stock,
            'total_value': round(total_value or 0, 2)
        }
        print(json.dumps(stats, indent=2))
        
        conn.close()
    except Exception as e:
        print(f"ERROR: Failed to query database: {e}")

def main():
    """Main function"""
    # Paths to check
    paths = [
        os.path.join(app_dir, 'app', 'data', 'quincaillerie.db'),
        os.path.join(app_dir, 'app', 'db', 'quincaillerie.db'),
        os.path.join(app_dir, 'db', 'quincaillerie.db')
    ]
    
    print("Direct Database Access Test")
    
    # Check environment variable path first if available
    if 'DATABASE_PATH' in os.environ:
        print(f"DATABASE_PATH environment variable is set to: {os.environ['DATABASE_PATH']}")
        check_database(os.environ['DATABASE_PATH'])
    
    # Check all paths
    for path in paths:
        check_database(path)

if __name__ == "__main__":
    main()
