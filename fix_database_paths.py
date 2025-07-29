#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Database Path Issues
This script ensures all database paths are correctly pointing to the same database
"""

import os
import sys
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

def backup_file(file_path):
    """Create a backup of a file"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup of {file_path} to {backup_path}")
        return True
    return False

def copy_database(source_path, dest_path):
    """Copy a database file from source to destination"""
    if os.path.exists(source_path):
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Backup existing destination file if it exists
        if os.path.exists(dest_path):
            backup_file(dest_path)
        
        # Copy the source file to the destination
        shutil.copy2(source_path, dest_path)
        logger.info(f"Copied database from {source_path} to {dest_path}")
        return True
    else:
        logger.error(f"Source database {source_path} does not exist")
        return False

def update_redirector():
    """Update the redirector module to always use the correct database path"""
    redirector_path = os.path.join(app_dir, 'db', 'database.py')
    
    if os.path.exists(redirector_path):
        # Backup the file
        backup_file(redirector_path)
        
        # New content for the redirector
        new_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Module Redirect
This file redirects imports from 'db.database' to 'app.db.database'
"""

import os
import sys
import logging

# Get the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (one level up)
project_dir = os.path.dirname(current_dir)

# Always use the data database regardless of any other environment settings
os.environ['DATABASE_PATH'] = os.path.join(project_dir, 'app', 'data', 'quincaillerie.db')

logger = logging.getLogger(__name__)
logger.info(f"Database redirector setting DATABASE_PATH to: {os.environ['DATABASE_PATH']}")

# Import everything from app.db.database
from app.db.database import *
'''
        
        # Write the new content
        with open(redirector_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Updated redirector at {redirector_path}")
        return True
    else:
        logger.error(f"Redirector file {redirector_path} does not exist")
        return False

def fix_app_js_debug():
    """Add debug logging to JavaScript files"""
    inventory_path = os.path.join(app_dir, 'app', 'templates', 'inventory.html')
    sales_path = os.path.join(app_dir, 'app', 'templates', 'sales.html')
    
    # Fix inventory.html
    if os.path.exists(inventory_path):
        with open(inventory_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace loadProducts function
        if 'async function loadProducts()' in content:
            updated = False
            
            # Only update if our debug logging isn't already there
            if 'console.log(\'API Response:\'' not in content:
                # Replace loadProducts function
                old_section = '''    // Load products from API
    async function loadProducts() {
        if (isLoading) return;
        
        isLoading = true;
        showLoading();
        
        try {
            const searchTerm = document.getElementById('searchInput').value;
            const category = document.getElementById('categoryFilter').value;
            const stockFilter = document.getElementById('stockFilter').value;

            const params = new URLSearchParams();
            if (searchTerm) params.append('search', searchTerm);
            if (category) params.append('category', category);
            if (stockFilter === 'low_stock' || stockFilter === 'out_of_stock') {
                params.append('low_stock', 'true');
            }
            
            const response = await fetch(`/api/inventory/products?${params}`);
            const data = await response.json();
            
            if (data.success) {
                currentProducts = data.products;
                displayProducts();
                updateStats(data.stats);
            } else {
                showNotification('Erreur lors du chargement des produits', 'error');
            }
        } catch (error) {
            console.error('Error loading products:', error);
            showNotification('Erreur de connexion', 'error');
        } finally {'''
                
                new_section = '''    // Load products from API
    async function loadProducts() {
        if (isLoading) return;
        
        isLoading = true;
        showLoading();
        
        try {
            const searchTerm = document.getElementById('searchInput').value;
            const category = document.getElementById('categoryFilter').value;
            const stockFilter = document.getElementById('stockFilter').value;

            const params = new URLSearchParams();
            if (searchTerm) params.append('search', searchTerm);
            if (category) params.append('category', category);
            if (stockFilter === 'low_stock' || stockFilter === 'out_of_stock') {
                params.append('low_stock', 'true');
            }
            
            console.log('Fetching products with params:', params.toString());
            const response = await fetch(`/api/inventory/products?${params}`);
            const data = await response.json();
            
            console.log('API Response:', data);
            
            if (data.success) {
                currentProducts = data.products;
                console.log(`Loaded ${currentProducts.length} products`);
                displayProducts();
                updateStats(data.stats);
                console.log('Stats updated:', data.stats);
            } else {
                console.error('API error:', data.message);
                showNotification('Erreur lors du chargement des produits', 'error');
            }
        } catch (error) {
            console.error('Error loading products:', error);
            showNotification('Erreur de connexion', 'error');
        } finally {'''
                
                if old_section in content:
                    content = content.replace(old_section, new_section)
                    updated = True
            
            if updated:
                backup_file(inventory_path)
                with open(inventory_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Added debug logging to {inventory_path}")
            else:
                logger.info(f"No changes needed for {inventory_path}")
        else:
            logger.warning(f"Could not find loadProducts function in {inventory_path}")
    
    # Fix sales.html
    if os.path.exists(sales_path):
        with open(sales_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace customers fetch
        if '// Load customers list' in content:
            updated = False
            
            # Only update if our debug logging isn't already there
            if 'console.log(\'Customers API response:\'' not in content:
                # Replace customers fetch
                old_section = '''                    // Load customers list
                    fetch('/api/customers')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                this.customers = data.customers || [];
                            }
                        })
                        .catch(error => console.error('Error loading customers:', error));'''
                
                new_section = '''                    // Load customers list
                    fetch('/api/customers')
                        .then(response => response.json())
                        .then(data => {
                            console.log('Customers API response:', data);
                            if (data.success) {
                                this.customers = data.customers || [];
                                console.log(`Loaded ${this.customers.length} customers:`, this.customers);
                            }
                        })
                        .catch(error => console.error('Error loading customers:', error));'''
                
                if old_section in content:
                    content = content.replace(old_section, new_section)
                    updated = True
            
            if updated:
                backup_file(sales_path)
                with open(sales_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Added debug logging to {sales_path}")
            else:
                logger.info(f"No changes needed for {sales_path}")
        else:
            logger.warning(f"Could not find customers fetch in {sales_path}")

def main():
    """Main function"""
    logger.info("Starting database path fix script")
    
    # Define paths
    data_db_path = os.path.join(app_dir, 'app', 'data', 'quincaillerie.db')
    db_db_path = os.path.join(app_dir, 'app', 'db', 'quincaillerie.db')
    
    # Make sure the right database is in both locations
    if os.path.exists(data_db_path):
        logger.info(f"Using {data_db_path} as the primary database")
        
        # Copy data database to db directory
        copy_database(data_db_path, db_db_path)
    elif os.path.exists(db_db_path):
        logger.info(f"Using {db_db_path} as the primary database")
        
        # Copy db database to data directory
        copy_database(db_db_path, data_db_path)
    else:
        logger.error("No database file found in either location!")
        return
    
    # Update the redirector module
    update_redirector()
    
    # Add debug logging to JavaScript files
    fix_app_js_debug()
    
    logger.info("Database path fix script completed")

if __name__ == "__main__":
    main()
