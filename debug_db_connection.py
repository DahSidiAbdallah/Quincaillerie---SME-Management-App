#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug database connection and verify data exists
"""

import os
import sys
import sqlite3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add app directory to Python path
app_dir = os.path.join(script_dir, 'app')
sys.path.insert(0, script_dir)
sys.path.append(app_dir)

# Check all potential database paths
def check_database_paths():
    """Check all potential database paths"""
    paths_to_check = [
        os.path.join(app_dir, 'data', 'quincaillerie.db'),
        os.path.join(app_dir, 'db', 'quincaillerie.db'),
        os.path.join(script_dir, 'app', 'data', 'quincaillerie.db'),
        os.path.join(script_dir, 'app', 'db', 'quincaillerie.db')
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            logger.info(f"✅ Database found at: {path} (Size: {size_kb:.2f} KB)")
            check_database_content(path)
        else:
            logger.warning(f"❌ No database at: {path}")

def check_database_content(db_path):
    """Check database content to see if it has the expected data"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check products
        cursor.execute("SELECT COUNT(*) as count FROM products")
        product_count = cursor.fetchone()['count']
        logger.info(f"📦 Products: {product_count}")
        
        # Check customers
        cursor.execute("SELECT COUNT(*) as count FROM customers")
        customer_count = cursor.fetchone()['count']
        logger.info(f"👥 Customers: {customer_count}")
        
        # Check sales
        cursor.execute("SELECT COUNT(*) as count FROM sales")
        sales_count = cursor.fetchone()['count']
        logger.info(f"💰 Sales: {sales_count}")
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        logger.info(f"📋 Tables in database: {', '.join(tables)}")
        
        # Check first few products
        logger.info("Sample products:")
        cursor.execute("SELECT id, name, category, current_stock FROM products LIMIT 5")
        for row in cursor.fetchall():
            logger.info(f"  - {row['id']}: {row['name']} ({row['category']}) - Stock: {row['current_stock']}")
        
        conn.close()
    except Exception as e:
        logger.error(f"Error checking database content: {e}")

def check_database_manager():
    """Check database manager import and operation"""
    try:
        logger.info("Attempting to import DatabaseManager...")
        
        try:
            from app.data.database import DatabaseManager
            logger.info("✅ Imported DatabaseManager from app.data.database")
            dm_path = "app.data.database.DatabaseManager"
        except ImportError:
            try:
                from db.database import DatabaseManager
                logger.info("✅ Imported DatabaseManager from db.database")
                dm_path = "db.database.DatabaseManager"
            except ImportError:
                logger.error("❌ Could not import DatabaseManager")
                return
        
        logger.info(f"Creating DatabaseManager instance from {dm_path}")
        db_manager = DatabaseManager()
        logger.info(f"DB Path according to DatabaseManager: {db_manager.db_path}")
        
        # Try to get connection
        conn = db_manager.get_connection()
        logger.info("✅ Successfully connected to the database using DatabaseManager")
        
        # Get product count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        logger.info(f"Product count from DatabaseManager: {product_count}")
        
        # Get a couple of products
        cursor.execute("SELECT id, name FROM products LIMIT 5")
        products = cursor.fetchall()
        logger.info(f"First few products: {[dict(p) for p in products]}")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error with DatabaseManager: {e}")

if __name__ == "__main__":
    logger.info("🔍 Starting database connection debug...")
    
    # Check all potential database paths
    check_database_paths()
    
    # Check DatabaseManager
    check_database_manager()
    
    logger.info("✅ Database debug complete")
