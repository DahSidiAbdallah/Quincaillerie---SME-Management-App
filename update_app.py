#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive update script to ensure all fixes are applied before running the app
"""

import os
import sys
import logging
import shutil
import sqlite3
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get project directories
project_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(project_dir, 'app')
db_dir = os.path.join(app_dir, 'db')
templates_dir = os.path.join(app_dir, 'templates')
data_dir = os.path.join(app_dir, 'data')
api_dir = os.path.join(app_dir, 'api')

def ensure_database_integrity():
    """Make sure the database is properly set up and has all needed tables"""
    db_path = os.path.join(data_dir, 'quincaillerie.db')
    
    logger.info(f"Checking database integrity at {db_path}")
    
    # Verify database exists
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}")
        return False
    
    try:
        # Check database structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for required tables
        required_tables = ['users', 'products', 'customers', 'sales', 'sale_items']
        
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone() is None:
                logger.error(f"Required table '{table}' not found in database")
                return False
                
        logger.info("All required tables present in the database")
        
        # Check if customer_id column exists in sales table
        cursor.execute("PRAGMA table_info(sales)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'customer_id' not in columns:
            logger.info("Adding customer_id column to sales table")
            cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER")
            
            # Link sales to customers
            cursor.execute("SELECT id, name, phone FROM customers")
            customers = {(row[1], row[2]): row[0] for row in cursor.fetchall()}
            
            cursor.execute("SELECT id, customer_name, customer_phone FROM sales")
            sales = cursor.fetchall()
            
            for sale_id, customer_name, customer_phone in sales:
                customer_key = (customer_name, customer_phone)
                if customer_key in customers:
                    cursor.execute("UPDATE sales SET customer_id = ? WHERE id = ?", 
                                 (customers[customer_key], sale_id))
            
            conn.commit()
            logger.info("Added customer_id column and linked sales to customers")
        
        # Verify customers data
        cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = 1")
        active_customer_count = cursor.fetchone()[0]
        logger.info(f"Active customers in database: {active_customer_count}")
        
        # Verify sales data
        cursor.execute("SELECT COUNT(*) FROM sales")
        sales_count = cursor.fetchone()[0]
        logger.info(f"Sales records in database: {sales_count}")
        
        # Verify inventory data
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        active_products_count = cursor.fetchone()[0]
        logger.info(f"Active products in database: {active_products_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking database integrity: {e}")
        return False

def fix_database_manager():
    """Fix the get_customers_list method in database.py"""
    database_py_path = os.path.join(db_dir, 'database.py')
    
    logger.info(f"Fixing DatabaseManager in {database_py_path}")
    
    try:
        # Create backup
        backup_path = os.path.join(db_dir, 'database.py.backup')
        shutil.copy2(database_py_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        
        # Read file
        with open(database_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix get_customers_list method
        import re
        pattern = r'def get_customers_list\(self\):.*?ORDER BY name'
        replacement = '''def get_customers_list(self):
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
                ORDER BY id"""
        )
        '''
        
        # Use regex with DOTALL to match across multiple lines
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write updated content
        with open(database_py_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        logger.info("Updated get_customers_list method in database.py")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing database manager: {e}")
        return False

def fix_sales_api():
    """Fix the sales API to return all sales by default"""
    sales_py_path = os.path.join(api_dir, 'sales.py')
    
    logger.info(f"Fixing sales API in {sales_py_path}")
    
    try:
        # Create backup
        backup_path = os.path.join(api_dir, 'sales.py.backup')
        shutil.copy2(sales_py_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        
        # Read file
        with open(sales_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix sales API to not default to today's date
        import re
        pattern = r"# Default: show only sales from today if no date filter specified.*?params\.append\(today_date\)"
        replacement = "# No default date filter, show all sales"
        
        # Use regex with DOTALL to match across multiple lines
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write updated content
        with open(sales_py_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        logger.info("Updated sales API to return all sales by default")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing sales API: {e}")
        return False

def fix_sales_template():
    """Fix the sales.html template to properly display stats and add period filter"""
    sales_html_path = os.path.join(templates_dir, 'sales.html')
    
    logger.info(f"Fixing sales template in {sales_html_path}")
    
    try:
        # Create backup
        backup_path = os.path.join(templates_dir, 'sales.html.backup')
        shutil.copy2(sales_html_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        
        # Read file
        with open(sales_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Import regex
        import re
        
        # Initialize updated_content with the original content
        updated_content = content
            
        # 1. Add period filter
        if "filterDate" not in content:
            # Find the status filter dropdown
            status_filter_pattern = r'<select x-model="filterStatus" class="border border-gray-300 rounded-md px-3 py-2 text-sm">.*?</select>'
            
            # Prepare the period filter HTML
            period_filter_html = """<select x-model="filterDate" @change="loadData()" class="border border-gray-300 rounded-md px-3 py-2 text-sm">
                            <option value="all">Toutes les périodes</option>
                            <option value="today">Aujourd'hui</option>
                            <option value="week">7 derniers jours</option>
                            <option value="month">30 derniers jours</option>
                        </select>"""
            
            # Find the status filter and add the period filter after it
            updated_content = re.sub(status_filter_pattern, lambda m: m.group(0) + "\n                        " + period_filter_html, updated_content, flags=re.DOTALL)
            
            # Initialize filterDate in the Alpine.js component
            updated_content = updated_content.replace("function salesManager() {", """function salesManager() {
                return {
                    filterDate: 'all',""")
            
            updated_content = updated_content.replace("return {", "")
            
            # Fix the loadData method to use filterDate
            data_method_pattern = r'loadData\(\) {.*?if \(this\.filterDate === \'today\'\)'
            if "filterDate" not in updated_content:
                updated_content = re.sub(data_method_pattern, 
                    """loadData() {
                    // Fetch data from the server
                    const url = new URL('/api/sales', window.location.origin);
                    
                    // Always set a high limit to get all records initially
                    url.searchParams.append('limit', '100');
                    
                    // Add filter parameters
                    if (this.filterDate === 'today')""", 
                    updated_content, flags=re.DOTALL)
            
            # Initialize with filterDate=all on page load
            updated_content = updated_content.replace('x-data="salesManager()"', 'x-data="salesManager()" x-init="$nextTick(() => { filterDate = \'all\'; loadData(); })"')
        
        # 2. Fix stats loading
        stats_method_pattern = r'loadStats\(\) {.*?},'
        updated_stats_method = """loadStats() {
                    // Fetch stats from the server
                    fetch('/api/sales/stats')
                        .then(response => response.json())
                        .then(data => {
                            console.log('Stats API response:', data);
                            if (data.success) {
                                this.stats = data.stats || this.stats;
                                
                                // Make sure we update client count from customers array if available
                                if (this.customers && this.customers.length > 0) {
                                    this.stats.active_customers = this.customers.length;
                                }
                                
                                // Count today's sales from sales array if needed
                                if (this.stats.today_sales === 0 && this.sales && this.sales.length > 0) {
                                    const today = new Date().toISOString().split('T')[0];
                                    const todaySales = this.sales.filter(sale => 
                                        sale.sale_date && sale.sale_date.startsWith(today)
                                    ).length;
                                    if (todaySales > 0) {
                                        this.stats.today_sales = todaySales;
                                    }
                                }
                            }
                        })
                        .catch(error => console.error('Error loading stats:', error));
                },"""
        
        updated_content = re.sub(stats_method_pattern, updated_stats_method, updated_content, flags=re.DOTALL)
        
        # Write updated content
        with open(sales_html_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        logger.info("Updated sales.html template with period filter and fixed stats")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing sales template: {e}")
        return False

def clean_pycache():
    """Clean __pycache__ directories to ensure new code is loaded"""
    logger.info("Cleaning __pycache__ directories")
    
    try:
        # Find and remove all __pycache__ directories
        for root, dirs, files in os.walk(project_dir):
            if '__pycache__' in dirs:
                pycache_dir = os.path.join(root, '__pycache__')
                shutil.rmtree(pycache_dir)
                logger.info(f"Removed {pycache_dir}")
        
        logger.info("All __pycache__ directories have been cleaned")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning __pycache__ directories: {e}")
        return False

def main():
    """Main function to run all updates"""
    logger.info("Starting comprehensive update before running the app")
    
    # Step 1: Check and fix database integrity
    if not ensure_database_integrity():
        logger.error("Database integrity check failed. Please fix database issues before continuing.")
        return
        
    # Step 2: Fix database manager
    if not fix_database_manager():
        logger.warning("Failed to fix database manager. Some features might not work correctly.")
    
    # Step 3: Fix sales API
    if not fix_sales_api():
        logger.warning("Failed to fix sales API. Some features might not work correctly.")
    
    # Step 4: Fix sales template
    if not fix_sales_template():
        logger.warning("Failed to fix sales template. Some features might not work correctly.")
    
    # Step 5: Clean __pycache__ directories to ensure new code is loaded
    if not clean_pycache():
        logger.warning("Failed to clean __pycache__ directories. You might need to restart the application.")
    
    logger.info("All updates completed successfully. The app is ready to run.")
    logger.info("To start the app, run: python run_fixed.py")

if __name__ == "__main__":
    main()
