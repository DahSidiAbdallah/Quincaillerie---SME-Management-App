#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup admin user script for Quincaillerie & SME Management App
Creates initial admin user in the empty database
"""

import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_admin():
    """Setup the database with an admin user"""
    # Get database path from environment or use default
    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
    db_path = os.path.join(app_dir, 'data', 'quincaillerie.db')
    
    logger.info(f"Setting up database at: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists, create it if not
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            logger.info("Creating users table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    pin_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'employee',
                    language TEXT DEFAULT 'fr',
                    is_active BOOLEAN DEFAULT 1,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            # Create admin user
            admin_pin = '1234'  # Default admin PIN
            admin_pin_hash = generate_password_hash(admin_pin)
            logger.info("Creating admin user...")
            cursor.execute('''
                INSERT INTO users (username, pin_hash, role, language)
                VALUES (?, ?, ?, ?)
            ''', ('admin', admin_pin_hash, 'admin', 'fr'))
            logger.info("Admin user created with PIN: 1234")
        else:
            logger.info("Admin user already exists")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info("Database setup complete!")
        logger.info("You can now log in with username 'admin' and PIN '1234'")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_admin()
