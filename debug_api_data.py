#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to check API endpoints and database data
"""

import os
import sys
import json
import sqlite3
import logging

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

# Import DatabaseManager
from app.db.database import DatabaseManager

def check_database_directly():
    """Check database tables directly with SQL"""
    logger.info(f"Checking database directly: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check customers table
        cursor.execute("SELECT * FROM customers ORDER BY id")
        customers = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Customers directly from database: {len(customers)}")
        for customer in customers:
            logger.info(f"Customer: {json.dumps(customer, default=str)}")
        
        # Check sales table
        cursor.execute("SELECT * FROM sales ORDER BY id")
        sales = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Sales directly from database: {len(sales)}")
        for sale in sales:
            logger.info(f"Sale: {json.dumps(sale, default=str)}")
        
        conn.close()
    except Exception as e:
        logger.error(f"Error querying database directly: {e}")

def check_database_via_manager():
    """Check database using DatabaseManager methods"""
    logger.info("Checking database via DatabaseManager")
    
    try:
        db_manager = DatabaseManager()
        
        # Check customers
        customers = db_manager.get_customers_list()
        logger.info(f"Customers via DatabaseManager: {len(customers)}")
        for customer in customers:
            logger.info(f"Customer: {json.dumps(customer, default=str)}")
        
        # Check sales
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales ORDER BY id")
        sales = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Sales via direct query: {len(sales)}")
        for sale in sales:
            logger.info(f"Sale: {json.dumps(sale, default=str)}")
        
        # Check if sales API method exists
        if hasattr(db_manager, 'get_sales_list'):
            sales_list = db_manager.get_sales_list()
            logger.info(f"Sales via get_sales_list: {len(sales_list)}")
        else:
            logger.warning("db_manager does not have get_sales_list method")
            
            # Check for similar methods
            methods = [method for method in dir(db_manager) if 'sale' in method.lower() and callable(getattr(db_manager, method))]
            logger.info(f"Sales-related methods: {methods}")
            
            # Try using get_recent_sales if available
            if 'get_recent_sales' in methods:
                recent_sales = db_manager.get_recent_sales()
                logger.info(f"Sales via get_recent_sales: {len(recent_sales)}")
                for sale in recent_sales:
                    logger.info(f"Sale: {json.dumps(sale, default=str)}")
    
    except Exception as e:
        logger.error(f"Error checking database via manager: {e}")

def fix_customer_data():
    """Fix any issues with customer data"""
    logger.info("Checking for customer data issues")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if ID sequence is correct
        cursor.execute("SELECT id FROM customers ORDER BY id")
        ids = [row[0] for row in cursor.fetchall()]
        logger.info(f"Customer IDs: {ids}")
        
        # Check if there are any inactive customers
        cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = 0")
        inactive_count = cursor.fetchone()[0]
        logger.info(f"Inactive customers: {inactive_count}")
        
        # Set all customers to active
        cursor.execute("UPDATE customers SET is_active = 1")
        conn.commit()
        logger.info("Set all customers to active")
        
        # Verify all customers are now active
        cursor.execute("SELECT id, name, is_active FROM customers ORDER BY id")
        customers = cursor.fetchall()
        logger.info("Customers after update:")
        for customer in customers:
            logger.info(f"  ID: {customer[0]}, Name: {customer[1]}, Active: {customer[2]}")
        
        conn.close()
    except Exception as e:
        logger.error(f"Error fixing customer data: {e}")

def fix_sales_data():
    """Fix any issues with sales data"""
    logger.info("Checking for sales data issues")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if there are any sales with NULL customer_id
        cursor.execute("SELECT COUNT(*) FROM sales WHERE customer_id IS NULL")
        null_customer_count = cursor.fetchone()[0]
        logger.info(f"Sales with NULL customer_id: {null_customer_count}")
        
        # Update any sales with NULL customer_id to a valid customer
        if null_customer_count > 0:
            cursor.execute("SELECT id FROM customers ORDER BY id LIMIT 1")
            first_customer_id = cursor.fetchone()[0]
            
            cursor.execute("UPDATE sales SET customer_id = ? WHERE customer_id IS NULL", (first_customer_id,))
            conn.commit()
            logger.info(f"Updated {null_customer_count} sales with NULL customer_id to customer ID {first_customer_id}")
        
        conn.close()
    except Exception as e:
        logger.error(f"Error fixing sales data: {e}")

def main():
    """Main function"""
    logger.info("Starting database debug script")
    
    # Check database directly and via manager
    check_database_directly()
    check_database_via_manager()
    
    # Fix any issues found
    fix_customer_data()
    fix_sales_data()
    
    logger.info("Database debug script completed")

if __name__ == "__main__":
    main()
