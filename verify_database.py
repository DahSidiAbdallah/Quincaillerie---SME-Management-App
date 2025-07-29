#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify database contents to ensure we have the correct data
"""

import os
import sys
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

def check_database(db_path):
    """Check database contents"""
    logger.info(f"Checking database: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"Database file does not exist: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check products
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        logger.info(f"Products count: {product_count}")
        
        # Check customers
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        logger.info(f"Customers count: {customer_count}")
        
        # List all products
        cursor.execute("SELECT id, name, current_stock FROM products")
        logger.info("Products list:")
        for product in cursor.fetchall():
            logger.info(f"  ID: {product[0]}, Name: {product[1]}, Stock: {product[2]}")
        
        # List all customers
        cursor.execute("SELECT id, name FROM customers")
        logger.info("Customers list:")
        for customer in cursor.fetchall():
            logger.info(f"  ID: {customer[0]}, Name: {customer[1]}")
        
        conn.close()
        
        # Verify we have the correct data
        if product_count == 10 and customer_count == 4:
            logger.info("✅ Database has the correct data: 10 products and 4 customers")
            return True
        else:
            logger.error(f"❌ Database has incorrect data: {product_count} products and {customer_count} customers")
            return False
    
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False

def main():
    """Main function"""
    # Set path to the database
    db_path = os.path.join(app_dir, 'app', 'data', 'quincaillerie.db')
    
    # Check the database
    check_database(db_path)

if __name__ == "__main__":
    main()
