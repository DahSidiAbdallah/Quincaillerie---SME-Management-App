#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Diagnostic Tool for Quincaillerie App
Checks database connections and API responses
"""

import os
import sys
import json
import sqlite3
from urllib.parse import urljoin
import requests

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

def check_database(db_path):
    """Check if database exists and contains data"""
    print(f"\n--- Checking Database: {db_path} ---")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file does not exist at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check products
        if 'products' in tables:
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            print(f"Products count: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, name, current_stock FROM products LIMIT 5")
                print("Sample products:")
                for row in cursor.fetchall():
                    print(f"  ID: {row[0]}, Name: {row[1]}, Stock: {row[2]}")
        
        # Check customers
        if 'customers' in tables:
            cursor.execute("SELECT COUNT(*) FROM customers")
            count = cursor.fetchone()[0]
            print(f"Customers count: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, name FROM customers LIMIT 5")
                print("Sample customers:")
                for row in cursor.fetchall():
                    print(f"  ID: {row[0]}, Name: {row[1]}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        return False

def check_api_endpoint(base_url, endpoint):
    """Check if API endpoint returns data"""
    url = urljoin(base_url, endpoint)
    print(f"\n--- Checking API Endpoint: {url} ---")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"Status code: {response.status_code}")
            print(f"Success: {data.get('success', False)}")
            
            # Print summary of returned data
            if 'products' in data:
                print(f"Products returned: {len(data['products'])}")
                if data['products']:
                    print("Sample product:")
                    print(json.dumps(data['products'][0], indent=2))
            
            if 'customers' in data:
                print(f"Customers returned: {len(data['customers'])}")
                if data['customers']:
                    print("Sample customer:")
                    print(json.dumps(data['customers'][0], indent=2))
            
            if 'stats' in data:
                print("Stats:")
                print(json.dumps(data['stats'], indent=2))
            
            return True
        else:
            print(f"ERROR: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to connect to API: {e}")
        return False

def main():
    """Main function"""
    # Paths
    main_db_path = os.path.join(app_dir, 'app', 'data', 'quincaillerie.db')
    db_db_path = os.path.join(app_dir, 'app', 'db', 'quincaillerie.db')
    root_db_path = os.path.join(app_dir, 'db', 'quincaillerie.db')
    
    # Check databases
    print("=== Database Checks ===")
    main_db_exists = check_database(main_db_path)
    db_db_exists = check_database(db_db_path)
    root_db_exists = check_database(root_db_path)
    
    # Determine which database should be used
    if 'DATABASE_PATH' in os.environ:
        print(f"\nDATABASE_PATH environment variable is set to: {os.environ['DATABASE_PATH']}")
        check_database(os.environ['DATABASE_PATH'])
    
    # Check API endpoints
    print("\n=== API Endpoint Checks ===")
    base_url = "http://localhost:5000/api/"
    
    print("\nNOTE: The following checks will only work if the app is running.")
    print("If you see connection errors, make sure the app is running first.")
    
    try:
        check_api_endpoint(base_url, "inventory/products")
        check_api_endpoint(base_url, "inventory/stats")
        check_api_endpoint(base_url, "customers")
    except Exception as e:
        print(f"Failed to check API endpoints: {e}")
        print("Make sure the app is running before checking API endpoints.")

if __name__ == "__main__":
    main()
