#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create an admin user to use for testing
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Set database path
os.environ['DATABASE_PATH'] = os.path.join(app_dir, 'app', 'data', 'quincaillerie.db')

# Import DatabaseManager
from app.data.database import DatabaseManager

def main():
    """Create admin user for testing"""
    db_manager = DatabaseManager()
    
    try:
        # Create admin user
        user_id = db_manager.create_user(
            username="admin",
            pin="1234",  # Simple PIN for testing
            role="admin"
        )
        
        if user_id:
            logger.info(f"Created admin user with ID: {user_id}")
            logger.info("Username: admin")
            logger.info("PIN: 1234")
            logger.info("You can now login to the application with these credentials")
        else:
            logger.error("Failed to create admin user. User might already exist.")
            
            # Check if user exists
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role FROM users WHERE username = ?", ("admin",))
            user = cursor.fetchone()
            if user:
                logger.info(f"Admin user already exists with ID: {user[0]}")
                logger.info(f"Username: {user[1]}, Role: {user[2]}")
            conn.close()
    
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")

if __name__ == "__main__":
    main()
