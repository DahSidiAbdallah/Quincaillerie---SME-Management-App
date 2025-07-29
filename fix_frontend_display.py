#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix script for frontend display issues
"""

import os
import sys
import sqlite3
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Set database path
db_path = os.path.join(app_dir, 'app', 'data', 'quincaillerie.db')
os.environ['DATABASE_PATH'] = db_path

def fix_get_customers_list():
    """Fix get_customers_list method in database.py"""
    try:
        # First, let's back up the original file
        db_py_path = os.path.join(app_dir, 'app', 'db', 'database.py')
        backup_path = os.path.join(app_dir, 'app', 'db', 'database.py.bak')
        
        # Read original file
        with open(db_py_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        # Create backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        logger.info(f"Created backup of database.py at {backup_path}")
        
        # Find and replace the get_customers_list method
        new_method = '''    def get_customers_list(self):
        """Get list of active customers"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if dedicated customers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
        has_table = cursor.fetchone() is not None

        if has_table:
            cursor.execute("""
                SELECT id, name, phone
                FROM customers
                WHERE is_active = 1
                ORDER BY id
            """)
        else:
            # Fallback: derive customers from sales table
            cursor.execute("""
                SELECT MIN(rowid) as id, customer_name as name, customer_phone as phone
                FROM sales
                WHERE customer_name != ''
                GROUP BY customer_name, customer_phone
                ORDER BY customer_name
            """)
        
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return customers'''
        
        # Search for the method definition in the original content
        import re
        pattern = r'def get_customers_list\(self\):.*?return customers'
        replacement = new_method.strip()
        
        # Replace the method with re.DOTALL to match across multiple lines
        new_content = re.sub(pattern, replacement, original_content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(db_py_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info("Updated get_customers_list method in database.py")
        
    except Exception as e:
        logger.error(f"Error fixing get_customers_list: {e}")

def fix_sales_display():
    """Check and fix sales display in API and frontend"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if sales have customer_id field
        cursor.execute("PRAGMA table_info(sales)")
        columns = [column['name'] for column in cursor.fetchall()]
        
        needs_migration = 'customer_id' not in columns
        
        if needs_migration:
            logger.info("Sales table needs migration to add customer_id field")
            
            # Start a transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # 1. First get all customers
            cursor.execute("SELECT id, name, phone FROM customers")
            customers = {(row['name'], row['phone']): row['id'] for row in cursor.fetchall()}
            
            # 2. Add customer_id column if it doesn't exist
            cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER")
            
            # 3. Update sales with customer_id
            for customer_name, customer_phone in customers.keys():
                customer_id = customers[(customer_name, customer_phone)]
                cursor.execute("""
                    UPDATE sales 
                    SET customer_id = ? 
                    WHERE customer_name = ? AND customer_phone = ?
                """, (customer_id, customer_name, customer_phone))
            
            # 4. Add an index on customer_id
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id)")
            
            # Commit transaction
            cursor.execute("COMMIT")
            
            logger.info("Sales table migration completed successfully")
        
        # Check if there are any sales with NULL sale_date and fix if needed
        cursor.execute("SELECT COUNT(*) FROM sales WHERE sale_date IS NULL")
        null_dates = cursor.fetchone()[0]
        
        if null_dates > 0:
            logger.info(f"Found {null_dates} sales with NULL sale_date, fixing...")
            cursor.execute("UPDATE sales SET sale_date = CURRENT_TIMESTAMP WHERE sale_date IS NULL")
            conn.commit()
            
        # Check if there are any sales with future dates and fix if needed
        cursor.execute("SELECT COUNT(*) FROM sales WHERE DATE(sale_date) > DATE('now')")
        future_dates = cursor.fetchone()[0]
        
        if future_dates > 0:
            logger.info(f"Found {future_dates} sales with future dates, fixing...")
            cursor.execute("UPDATE sales SET sale_date = CURRENT_TIMESTAMP WHERE DATE(sale_date) > DATE('now')")
            conn.commit()
        
        # Check if all fields needed for frontend display are present
        cursor.execute("""
            SELECT s.id, s.sale_date, s.customer_name, s.total_amount, 
                   s.payment_method, s.status, COUNT(si.id) as items_count
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            GROUP BY s.id
            ORDER BY s.sale_date DESC
            LIMIT 5
        """)
        
        latest_sales = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Latest 5 sales: {json.dumps(latest_sales, default=str)}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error fixing sales display: {e}")

def main():
    """Main function"""
    logger.info("Starting fixes for frontend display issues")
    
    # Fix the get_customers_list method to preserve correct order
    fix_get_customers_list()
    
    # Fix sales display in the frontend
    fix_sales_display()
    
    logger.info("Fixes completed. Please restart the application for changes to take effect.")

if __name__ == "__main__":
    main()
