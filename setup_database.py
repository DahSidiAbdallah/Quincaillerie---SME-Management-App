#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Setup and Path Verification Script
This script ensures proper database initialization and consistent paths
"""

import os
import sys
import shutil
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project paths
project_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(project_dir, 'app')
data_dir = os.path.join(app_dir, 'data')
db_dir = os.path.join(app_dir, 'db')

# Make sure these directories exist
for directory in [data_dir, db_dir]:
    os.makedirs(directory, exist_ok=True)

# The canonical database path
canonical_db_path = os.path.join(data_dir, 'quincaillerie.db')
logger.info(f"Setting canonical database path to: {canonical_db_path}")

def backup_database(db_path):
    """Create a backup of an existing database"""
    if os.path.exists(db_path):
        backup_dir = os.path.join(project_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
        
        shutil.copy2(db_path, backup_path)
        logger.info(f"Created backup of {db_path} at {backup_path}")
        return True
    return False

def consolidate_database_paths():
    """Ensure database exists in the canonical location and remove duplicates"""
    # Possible database locations
    db_locations = [
        canonical_db_path,
        os.path.join(db_dir, 'quincaillerie.db')
    ]
    
    # Find the first existing database file
    existing_db = None
    for path in db_locations:
        if os.path.exists(path):
            existing_db = path
            logger.info(f"Found existing database at: {path}")
            break
    
    # If no database found, we'll create a new one at the canonical location
    if not existing_db:
        logger.info("No existing database found. Will create a new one.")
        return False
    
    # If the existing database is not at the canonical path, copy it there
    if existing_db != canonical_db_path:
        backup_database(existing_db)
        
        # Copy to canonical location
        os.makedirs(os.path.dirname(canonical_db_path), exist_ok=True)
        if os.path.exists(canonical_db_path):
            backup_database(canonical_db_path)
        
        shutil.copy2(existing_db, canonical_db_path)
        logger.info(f"Copied database to canonical location: {canonical_db_path}")
    
    # Create a symlink in the db directory if it's different
    alt_path = os.path.join(db_dir, 'quincaillerie.db')
    if alt_path != canonical_db_path:
        # If there's already a database at the alternate path, back it up
        if os.path.exists(alt_path):
            backup_database(alt_path)
            os.remove(alt_path)
        
        # On Windows, we create a copy instead of a symlink for simplicity
        shutil.copy2(canonical_db_path, alt_path)
        logger.info(f"Created database copy at: {alt_path}")
    
    return True

def verify_database_integrity():
    """Check if the database is valid and has all expected tables"""
    if not os.path.exists(canonical_db_path):
        logger.error(f"Database does not exist at {canonical_db_path}")
        return False
    
    try:
        conn = sqlite3.connect(canonical_db_path)
        cursor = conn.cursor()
        
        # Check for essential tables
        required_tables = ['users', 'products', 'customers', 'sales']
        missing_tables = []
        
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            logger.warning(f"Database is missing these tables: {missing_tables}")
            return False
            
        # Check if users table has at least one user
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            logger.warning("No users found in the database. You'll need to create an admin user.")
        
        conn.close()
        logger.info("Database integrity verified successfully")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database verification failed: {e}")
        return False

def create_redirector():
    """Create or update the database redirector in db directory"""
    redirector_path = os.path.join(db_dir, 'database.py')
    
    # Backup existing file if needed
    if os.path.exists(redirector_path):
        backup_path = f"{redirector_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy2(redirector_path, backup_path)
    
    # Create redirector content
    redirector_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Redirector Module
Ensures consistent database access by importing from app.data.database
"""

import os
import sys
import logging

# Get the absolute paths
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
data_dir = os.path.join(app_dir, 'data')
canonical_db_path = os.path.join(data_dir, 'quincaillerie.db')

# Set database path environment variable
os.environ['DATABASE_PATH'] = canonical_db_path

logger = logging.getLogger(__name__)
logger.info(f"Database redirector setting DATABASE_PATH to: {{os.environ['DATABASE_PATH']}}")

# Import everything from the main database module
from app.data.database import *
'''
    
    # Write the redirector file
    with open(redirector_path, 'w', encoding='utf-8') as f:
        f.write(redirector_content)
    
    logger.info(f"Created database redirector at {redirector_path}")
    return True

def main():
    """Main execution function"""
    logger.info("Starting database setup and path verification...")
    
    # Set up Python path for imports
    sys.path.insert(0, project_dir)
    sys.path.append(app_dir)
    
    # Set database path environment variable
    os.environ['DATABASE_PATH'] = canonical_db_path
    
    # Step 1: Consolidate database paths
    consolidated = consolidate_database_paths()
    
    # Step 2: Create redirector module
    create_redirector()
    
    # Step 3: Import and initialize database if needed
    if not consolidated or not verify_database_integrity():
        logger.info("Initializing database...")
        
        try:
            # Import the database manager from the canonical location
            sys.path.append(data_dir)
            from app.data.database import DatabaseManager
            
            # Initialize database
            db_manager = DatabaseManager(canonical_db_path)
            db_manager.init_database()
            
            # Verify the database was created
            if os.path.exists(canonical_db_path):
                logger.info(f"Database initialized successfully at {canonical_db_path}")
                
                # Verify database integrity again
                if not verify_database_integrity():
                    logger.warning("Database created but verification failed - may be missing tables")
            else:
                logger.error("Failed to create database")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Step 4: Create admin user if needed
    create_admin = False
    try:
        conn = sqlite3.connect(canonical_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        
        if user_count == 0:
            create_admin = True
    except Exception as e:
        logger.error(f"Error checking user count: {e}")
    
    if create_admin:
        logger.info("No users found. Creating admin user...")
        try:
            # Try to run the create_admin.py script
            create_admin_script = os.path.join(project_dir, 'create_admin.py')
            if os.path.exists(create_admin_script):
                # Ensure the database path is properly set before importing
                os.environ['DATABASE_PATH'] = canonical_db_path
                
                # Run the script
                exec(open(create_admin_script).read())
                logger.info("Admin user created successfully")
            else:
                logger.warning(f"Could not find create_admin.py script at {create_admin_script}")
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
    
    logger.info("Database setup complete!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
