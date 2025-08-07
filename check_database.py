#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to check database contents
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Add the current directory to the Python path for absolute imports
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_dir)
    
    # Add the app directory to the Python path for relative imports
    app_dir = os.path.join(project_dir, 'app')
    sys.path.append(app_dir)
    
    # Add the db directory to the Python path
    db_dir = os.path.join(project_dir, 'app', 'db')
    sys.path.append(db_dir)
    
    # Set environment variables before importing the app
    os.environ['DATABASE_PATH'] = os.path.join(app_dir, 'data', 'quincaillerie.db')
    logger.info(f"Using database: {os.environ['DATABASE_PATH']}")
    
    try:
        from app.data.database import DatabaseManager
        
        # Create an instance of DatabaseManager
        db_manager = DatabaseManager()
        
        # Check database contents
        logger.info("Checking database contents...")
        
        # Check products
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        logger.info(f"Number of products: {product_count}")
        
        # Check customers
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        logger.info(f"Number of customers: {customer_count}")
        
        # Check sales
        cursor.execute("SELECT COUNT(*) FROM sales")
        sales_count = cursor.fetchone()[0]
        logger.info(f"Number of sales: {sales_count}")
        
        # Get inventory stats
        inventory_stats = db_manager.get_inventory_stats()
        logger.info(f"Inventory stats: {inventory_stats}")
        
        # Get sales stats
        sales_stats = db_manager.get_sales_stats()
        logger.info(f"Sales stats: {sales_stats}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking database contents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
