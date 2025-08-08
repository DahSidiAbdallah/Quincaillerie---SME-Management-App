#!/usr/bin/env python3
"""
Fix settings table schema mismatch
The code expects individual columns but database has key-value structure
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.data.database import DatabaseManager

def fix_settings_schema():
    """Fix settings table schema to match code expectations"""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        print("🔧 Fixing settings table schema...")
        
        # Check current table structure
        cursor.execute("PRAGMA table_info(settings)")
        current_columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {current_columns}")
        
        # Check if we have the old key-value structure
        if 'key' in current_columns and 'value' in current_columns:
            print("Found key-value structure, converting to column structure...")
            
            # Get existing settings data
            cursor.execute("SELECT key, value FROM settings")
            settings_data = dict(cursor.fetchall())
            print(f"Existing settings: {settings_data}")
            
            # Drop the old table
            cursor.execute("DROP TABLE settings")
            
            # Create new table with proper structure
            cursor.execute('''
                CREATE TABLE settings (
                    id INTEGER PRIMARY KEY,
                    store_name TEXT DEFAULT 'Quincaillerie',
                    store_address TEXT,
                    store_phone TEXT,
                    tax_rate REAL DEFAULT 0.0,
                    currency TEXT DEFAULT 'MRU',
                    language TEXT DEFAULT 'fr',
                    low_stock_threshold INTEGER DEFAULT 5,
                    ai_features_enabled BOOLEAN DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default settings with any existing data
            store_name = settings_data.get('store_name', 'Quincaillerie')
            store_address = settings_data.get('store_address', '')
            store_phone = settings_data.get('store_phone', '')
            tax_rate = float(settings_data.get('tax_rate', 0.0))
            currency = settings_data.get('currency', 'MRU')
            language = settings_data.get('language', 'fr')
            low_stock_threshold = int(settings_data.get('low_stock_threshold', 5))
            ai_features_enabled = bool(settings_data.get('ai_features_enabled', True))
            
            cursor.execute('''
                INSERT INTO settings (
                    id, store_name, store_address, store_phone, tax_rate, 
                    currency, language, low_stock_threshold, ai_features_enabled
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (store_name, store_address, store_phone, tax_rate, 
                  currency, language, low_stock_threshold, ai_features_enabled))
            
            print("✅ Successfully converted settings table to column structure")
            
        elif 'store_name' in current_columns:
            print("Settings table already has correct column structure")
            
            # Check if data exists
            cursor.execute("SELECT COUNT(*) FROM settings")
            count = cursor.fetchone()[0]
            
            if count == 0:
                print("No settings data found, inserting defaults...")
                cursor.execute('''
                    INSERT INTO settings (
                        id, store_name, store_address, store_phone, tax_rate, 
                        currency, language, low_stock_threshold, ai_features_enabled
                    ) VALUES (1, 'Quincaillerie', '', '', 0.0, 'MRU', 'fr', 5, 1)
                ''')
                print("✅ Inserted default settings")
        else:
            print("❌ Unrecognized settings table structure")
            return False
        
        conn.commit()
        
        # Verify the fix
        cursor.execute("PRAGMA table_info(settings)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"New columns: {new_columns}")
        
        cursor.execute("SELECT * FROM settings WHERE id = 1")
        settings_row = cursor.fetchone()
        if settings_row:
            print(f"Settings data: {dict(settings_row)}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error fixing settings schema: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_settings_schema()
    if success:
        print("\n🎉 Settings table schema fix completed!")
    else:
        print("\n💥 Settings table schema fix failed!")
