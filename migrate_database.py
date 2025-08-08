#!/usr/bin/env python3
"""
Database migration script to add missing columns to existing databases
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.data.database import DatabaseManager

class DatabaseMigrator:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.migrations = []
        
    def add_migration(self, name, sql_commands):
        """Add a migration to the list"""
        self.migrations.append({
            'name': name,
            'sql': sql_commands,
            'timestamp': datetime.now().isoformat()
        })
    
    def check_column_exists(self, table_name, column_name):
        """Check if a column exists in a table"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return column_name in columns
        except Exception as e:
            print(f"Error checking column {column_name} in {table_name}: {e}")
            return False
        finally:
            conn.close()
    
    def execute_migration(self, migration):
        """Execute a single migration"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            for sql_command in migration['sql']:
                print(f"Executing: {sql_command}")
                cursor.execute(sql_command)
            
            conn.commit()
            print(f"✅ Migration '{migration['name']}' completed successfully")
            return True
        except Exception as e:
            conn.rollback()
            print(f"❌ Migration '{migration['name']}' failed: {e}")
            return False
        finally:
            conn.close()
    
    def run_migrations(self):
        """Run all pending migrations"""
        print("🔧 Starting database migrations...")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add missing columns to settings table
        settings_columns = [
            ('currency', "ALTER TABLE settings ADD COLUMN currency TEXT DEFAULT 'MRU'"),
            ('backup_frequency', "ALTER TABLE settings ADD COLUMN backup_frequency TEXT DEFAULT 'daily'"),
            ('email_notifications', "ALTER TABLE settings ADD COLUMN email_notifications BOOLEAN DEFAULT 1"),
            ('auto_backup', "ALTER TABLE settings ADD COLUMN auto_backup BOOLEAN DEFAULT 1")
        ]
        
        for column_name, alter_sql in settings_columns:
            if not self.check_column_exists('settings', column_name):
                self.add_migration(
                    f"Add {column_name} to settings table",
                    [alter_sql]
                )
            else:
                print(f"⏭️  Column '{column_name}' already exists in settings table")
        
        # Add missing columns to users table if needed
        users_columns = [
            ('language', "ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'fr'"),
            ('is_active', "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"),
            ('email', "ALTER TABLE users ADD COLUMN email TEXT"),
            ('phone', "ALTER TABLE users ADD COLUMN phone TEXT")
        ]
        
        for column_name, alter_sql in users_columns:
            if not self.check_column_exists('users', column_name):
                self.add_migration(
                    f"Add {column_name} to users table",
                    [alter_sql]
                )
            else:
                print(f"⏭️  Column '{column_name}' already exists in users table")
        
        # Execute all migrations
        success_count = 0
        total_migrations = len(self.migrations)
        
        if total_migrations == 0:
            print("✅ No migrations needed - database is up to date!")
            return True
        
        print(f"\n📋 Found {total_migrations} migrations to execute:")
        for i, migration in enumerate(self.migrations, 1):
            print(f"  {i}. {migration['name']}")
        
        print("\n🚀 Executing migrations...")
        for migration in self.migrations:
            if self.execute_migration(migration):
                success_count += 1
        
        print("\n" + "="*60)
        print("📊 MIGRATION REPORT")
        print("="*60)
        print(f"Total Migrations: {total_migrations}")
        print(f"Successful: {success_count} ✅")
        print(f"Failed: {total_migrations - success_count} ❌")
        
        if success_count == total_migrations:
            print("🎉 All migrations completed successfully!")
            return True
        else:
            print("⚠️  Some migrations failed. Please check the errors above.")
            return False
    
    def verify_schema(self):
        """Verify the database schema after migrations"""
        print("\n🔍 Verifying database schema...")
        
        required_tables = ['users', 'settings', 'products', 'sales', 'activities']
        required_columns = {
            'settings': ['currency', 'backup_frequency', 'tax_rate', 'store_name'],
            'users': ['username', 'role', 'language', 'is_active']
        }
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table in existing_tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
            
            # Check columns exist
            for table_name, columns in required_columns.items():
                if table_name in existing_tables:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    table_columns = [row[1] for row in cursor.fetchall()]
                    
                    for column in columns:
                        if column in table_columns:
                            print(f"✅ Column '{table_name}.{column}' exists")
                        else:
                            print(f"❌ Column '{table_name}.{column}' missing")
        
        except Exception as e:
            print(f"Error during schema verification: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    migrator = DatabaseMigrator()
    
    # Run migrations
    success = migrator.run_migrations()
    
    # Verify schema
    migrator.verify_schema()
    
    if success:
        print("\n🎯 Database migration completed successfully!")
        print("You can now run the admin functionality tests again.")
    else:
        print("\n⚠️  Database migration had issues. Please check the errors above.")
