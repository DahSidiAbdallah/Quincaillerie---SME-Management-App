#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to populate the main database with Mauritanian data
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
    
    # Set database path to the main application database
    db_path = os.path.join(app_dir, 'data', 'quincaillerie.db')
    logger.info(f"Using database: {db_path}")
    
    # Create app/data directory if it doesn't exist
    data_dir = os.path.join(app_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        logger.info(f"Created directory: {data_dir}")
    
    try:
        # Import database manager
        from app.data.database import DatabaseManager
        
        # Set environment variable for database path
        os.environ['DATABASE_PATH'] = db_path
        
        # Create an instance of DatabaseManager
        db_manager = DatabaseManager()
        
        # Initialize the database
        logger.info("Initializing database schema...")
        db_manager.init_database()
        logger.info("Database schema initialized successfully.")
        
        # Populate with Mauritanian data
        logger.info("Populating database with Mauritanian data...")
        db_manager.populate_mauritania_data()
        logger.info("Database populated with Mauritanian data successfully!")
        
    except Exception as e:
        logger.error(f"Failed to populate database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
