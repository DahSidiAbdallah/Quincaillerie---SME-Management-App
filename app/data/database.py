#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Manager for Quincaillerie & SME Management App
Handles all database operations with SQLite (offline-first)
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path=None):
        """Initialize with a consistent database path."""
        env_path = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PATH')
        if env_path and env_path.startswith('sqlite:///'):
            env_path = env_path.replace('sqlite:///', '', 1)

        if env_path:
            self.db_path = os.path.abspath(env_path)
        else:
            default_path = os.path.join(os.path.dirname(__file__), 'quincaillerie.db')
            self.db_path = os.path.abspath(db_path or default_path)

        self.ensure_db_directory()
    
    def ensure_db_directory(self):
        """Ensure database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """Get database connection with row factory"""
        logger.debug(f"Connecting to database at: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Users table (Phase 1.1)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    pin_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'employee',
                    language TEXT DEFAULT 'fr',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # Customers table - used for sales and credit tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Products/Articles table (Phase 1.2)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    purchase_price REAL NOT NULL,
                    sale_price REAL NOT NULL,
                    selling_price REAL,
                    current_stock INTEGER DEFAULT 0,
                    min_stock_alert INTEGER DEFAULT 5,
                    category TEXT,
                    supplier TEXT,
                    barcode TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')

            # Ensure selling_price column exists (for compatibility)
            cursor.execute("PRAGMA table_info(products)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'selling_price' not in columns:
                cursor.execute('ALTER TABLE products ADD COLUMN selling_price REAL')
                # Copy sale_price to selling_price for existing records
                cursor.execute('UPDATE products SET selling_price = sale_price WHERE selling_price IS NULL')
            
            # Stock movements table (Phase 1.3)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    movement_type TEXT NOT NULL, -- 'in', 'out', 'adjustment'
                    quantity INTEGER NOT NULL,
                    unit_price REAL,
                    total_amount REAL,
                    reference TEXT, -- invoice/receipt reference
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # Sales table (Phase 1.3)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_date DATE NOT NULL,
                    invoice_number TEXT,
                    customer_name TEXT,
                    customer_phone TEXT,
                    total_amount REAL NOT NULL,
                    paid_amount REAL NOT NULL,
                    payment_method TEXT DEFAULT 'cash', -- 'cash', 'credit', 'mobile'
                    is_credit BOOLEAN DEFAULT 0,
                    credit_due_date DATE,
                    status TEXT DEFAULT 'completed', -- 'completed', 'pending', 'cancelled', 'paid', 'retard'
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')

            # Ensure required columns exist
            cursor.execute("PRAGMA table_info(sales)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'invoice_number' not in columns:
                cursor.execute('ALTER TABLE sales ADD COLUMN invoice_number TEXT')
            if 'is_deleted' not in columns:
                cursor.execute('ALTER TABLE sales ADD COLUMN is_deleted BOOLEAN DEFAULT 0')
            if 'updated_at' not in columns:
                cursor.execute('ALTER TABLE sales ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            
            # Sale items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    profit_margin REAL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Capital tracking table (Phase 1.4)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS capital_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    source TEXT NOT NULL,
                    justification TEXT,
                    has_receipt BOOLEAN DEFAULT 0,
                    receipt_image TEXT, -- file path
                    entry_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')

            # Ensure updated_at column exists
            cursor.execute("PRAGMA table_info(capital_entries)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'updated_at' not in columns:
                cursor.execute('ALTER TABLE capital_entries ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            
            # Expenses table (Phase 1.5)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL, -- 'business', 'personal'
                    subcategory TEXT, -- 'rent', 'electricity', 'supplies', etc.
                    description TEXT NOT NULL,
                    has_receipt BOOLEAN DEFAULT 0,
                    receipt_image TEXT, -- file path
                    expense_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')

            # Ensure required columns exist in expenses
            cursor.execute("PRAGMA table_info(expenses)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'updated_at' not in columns:
                cursor.execute('ALTER TABLE expenses ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            if 'is_deleted' not in columns:
                cursor.execute('ALTER TABLE expenses ADD COLUMN is_deleted BOOLEAN DEFAULT 0')
            
            # Client debts table (Phase 2.1)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS client_debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT NOT NULL,
                    client_phone TEXT,
                    client_address TEXT,
                    sale_id INTEGER,
                    total_amount REAL NOT NULL,
                    paid_amount REAL DEFAULT 0,
                    remaining_amount REAL NOT NULL,
                    due_date DATE,
                    status TEXT DEFAULT 'pending', -- 'pending', 'paid', 'overdue'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # Supplier debts table (Phase 2.2)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier_debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_name TEXT NOT NULL,
                    supplier_phone TEXT,
                    supplier_address TEXT,
                    invoice_reference TEXT,
                    total_amount REAL NOT NULL,
                    paid_amount REAL DEFAULT 0,
                    remaining_amount REAL NOT NULL,
                    due_date DATE,
                    status TEXT DEFAULT 'pending', -- 'pending', 'paid', 'overdue'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # Daily cash register table (Phase 2.3)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cash_register (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    register_date DATE UNIQUE NOT NULL,
                    opening_balance REAL DEFAULT 0,
                    closing_balance REAL DEFAULT 0,
                    total_sales REAL DEFAULT 0,
                    total_expenses REAL DEFAULT 0,
                    cash_in REAL DEFAULT 0,
                    cash_out REAL DEFAULT 0,
                    notes TEXT,
                    is_closed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # User activity log table (Phase 5.2)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL, -- 'login', 'sale', 'stock_update', etc.
                    description TEXT,
                    table_affected TEXT,
                    record_id INTEGER,
                    old_values TEXT, -- JSON
                    new_values TEXT, -- JSON
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'success',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # User profiles table (Phase 5.3)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT,
                    phone TEXT,
                    photo_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # User preferences table (Phase 5.3)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    preferences TEXT, -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Notification preferences table (Phase 5.3)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    preferences TEXT, -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Application wide settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # AI predictions cache table (Phase 4)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_type TEXT NOT NULL, -- 'stock_out', 'sales_forecast', 'restock_suggestion'
                    product_id INTEGER,
                    prediction_data TEXT NOT NULL, -- JSON
                    confidence_score REAL,
                    prediction_date DATE NOT NULL,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Sync queue for offline functionality
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    operation TEXT NOT NULL, -- 'insert', 'update', 'delete'
                    data TEXT, -- JSON
                    sync_status TEXT DEFAULT 'pending', -- 'pending', 'synced', 'failed'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_at TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(invoice_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_log_user ON user_activity_log(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_debts_status ON client_debts(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_supplier_debts_status ON supplier_debts(status)')
            
            # Create default admin user if not exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
            if cursor.fetchone()[0] == 0:
                admin_pin_hash = generate_password_hash('1234')  # Default admin PIN
                cursor.execute('''
                    INSERT INTO users (username, pin_hash, role, language) 
                    VALUES (?, ?, ?, ?)
                ''', ('admin', admin_pin_hash, 'admin', 'fr'))
                logger.info("Default admin user created with PIN: 1234")
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            conn.close()
    
    def authenticate_user(self, username, pin):
        """Authenticate user with username and PIN"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, pin_hash, role, language, is_active 
            FROM users WHERE username = ? AND is_active = 1
        ''', (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['pin_hash'], pin):
            # Update last login
            self.update_last_login(user['id'])
            return dict(user)
        return None
    
    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def create_user(self, user_data):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            pin_hash = generate_password_hash(user_data['pin'])
            cursor.execute('''
                INSERT INTO users (username, pin_hash, role, language) 
                VALUES (?, ?, ?, ?)
            ''', (
                user_data['username'], 
                pin_hash, 
                user_data.get('role', 'employee'), 
                user_data.get('language', 'fr')
            ))
            user_id = cursor.lastrowid
            conn.commit()
            logger.info(f"User {user_data['username']} created successfully")
            return {'success': True, 'user_id': user_id}
        except sqlite3.IntegrityError:
            conn.rollback()
            return {'success': False, 'error': "Nom d'utilisateur déjà existant"}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating user: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def update_user(self, user_id, data):
        """Update user information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            update_fields = []
            values = []
            
            for field in ['username', 'role', 'language', 'is_active']:
                if field in data:
                    update_fields.append(f'{field} = ?')
                    values.append(data[field])
            
            if 'new_pin' in data:
                update_fields.append('pin_hash = ?')
                values.append(generate_password_hash(data['new_pin']))
            
            if update_fields:
                values.append(user_id)
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, values)
                
                if cursor.rowcount == 0:
                    return {'success': False, 'error': 'Utilisateur non trouvé'}
                
                conn.commit()
                return {'success': True}
            else:
                return {'success': False, 'error': 'Aucune donnée à mettre à jour'}
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating user: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def delete_user(self, user_id):
        """Soft delete a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
            if cursor.rowcount == 0:
                return {'success': False, 'error': 'Utilisateur non trouvé'}
            
            conn.commit()
            return {'success': True}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting user: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_users(self):
        """Get all users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, role, language, created_at, last_login, is_active
            FROM users ORDER BY created_at DESC
        ''')
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users

    def upsert_user_by_username(self, user_data):
        """Insert or update user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if user exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (user_data['username'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing user
                user_id = existing['id']
                update_fields = []
                values = []
                
                for field in ['role', 'language', 'is_active']:
                    if field in user_data:
                        update_fields.append(f'{field} = ?')
                        values.append(user_data[field])
                
                if update_fields:
                    values.append(user_id)
                    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(query, values)
                
                conn.commit()
                return {'success': True, 'user_id': user_id, 'action': 'updated'}
            else:
                # Create new user
                return self.create_user(user_data)
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error upserting user: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def log_user_action(self, user_id, action_type, description, table_affected=None, record_id=None, old_values=None, new_values=None):
        """Log user action for audit trail"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_activity_log 
            (user_id, action_type, description, table_affected, record_id, old_values, new_values)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action_type, description, table_affected, record_id, 
              json.dumps(old_values) if old_values else None,
              json.dumps(new_values) if new_values else None))
        
        conn.commit()
        conn.close()
    
    def update_user_language(self, user_id, language):
        """Update user's preferred language"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET language = ? WHERE id = ?', (language, user_id))
        conn.commit()
        conn.close()

    # --- Application settings ---
    def get_app_settings(self):
        """Return application settings as dict"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM app_settings')
        data = {row['key']: row['value'] for row in cursor.fetchall()}
        conn.close()
        return data

    def set_app_settings(self, settings: dict):
        """Update application settings"""
        if not settings:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        for k, v in settings.items():
            cursor.execute('REPLACE INTO app_settings (key, value) VALUES (?, ?)', (k, json.dumps(v) if isinstance(v, (dict, list)) else str(v)))
        conn.commit()
        conn.close()
    
    # Dashboard data methods
    def get_total_products(self):
        """Get total number of active products"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM products WHERE is_active = 1')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_low_stock_items(self, limit=10):
        """Get products with low stock"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, current_stock, min_stock_alert 
            FROM products 
            WHERE is_active = 1 AND current_stock <= min_stock_alert 
            ORDER BY current_stock ASC LIMIT ?
        ''', (limit,))
        items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return items

    def get_inventory_stats(self):
        """Return inventory statistics for dashboard and inventory pages"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM products WHERE is_active = 1')
        total = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM products
            WHERE is_active = 1 AND current_stock > 0
        ''')
        in_stock = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM products
            WHERE is_active = 1 AND current_stock <= min_stock_alert
        ''')
        low_stock = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM products
            WHERE is_active = 1 AND current_stock = 0
        ''')
        out_of_stock = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COALESCE(SUM(purchase_price * current_stock), 0)
            FROM products WHERE is_active = 1
        ''')
        total_value = cursor.fetchone()[0]

        conn.close()

        result = {
            'total': total,
            'in_stock': in_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'inventory_value': round(total_value or 0, 2)
        }
        return result
    
    def get_today_sales(self):
        """Get today's sales summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Format today's date as YYYY-MM-DD to ensure consistency
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
            FROM sales WHERE DATE(sale_date) = ? AND (is_deleted IS NULL OR is_deleted = 0)
        ''', (today,))
        result = dict(cursor.fetchone())
        conn.close()
        return result
    
    def get_total_revenue(self):
        """Get total revenue from all sales"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE (is_deleted IS NULL OR is_deleted = 0)')
        total = cursor.fetchone()[0]
        conn.close()
        return total
    
    def get_pending_debts(self):
        """Get pending client debts summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(remaining_amount), 0) as total
            FROM client_debts WHERE status = 'pending'
        ''')
        result = dict(cursor.fetchone())
        conn.close()
        return result
    
    def get_cash_balance(self):
        """Get current cash balance from latest cash register"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT closing_balance FROM cash_register 
            ORDER BY register_date DESC LIMIT 1
        ''')
        result = cursor.fetchone()
        balance = result[0] if result else 0
        conn.close()
        return balance
    
    def get_recent_activities(self, limit=10):
        """Get recent user activities"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ual.action_type, ual.description, ual.created_at, u.username
            FROM user_activity_log ual
            JOIN users u ON ual.user_id = u.id
            ORDER BY ual.created_at DESC LIMIT ?
        ''', (limit,))
        activities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return activities
    
    def get_top_selling_products(self, days=30, limit=5):
        """Get top selling products for the dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Calculate the date from X days ago
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                p.id, 
                p.name,
                p.category,
                SUM(si.quantity) as quantity_sold,
                SUM(si.total_price) as total_sales
            FROM 
                sale_items si
                JOIN products p ON si.product_id = p.id
                JOIN sales s ON si.sale_id = s.id
            WHERE 
                s.sale_date >= ?
                AND p.is_active = 1
                AND (s.is_deleted IS NULL OR s.is_deleted = 0)
            GROUP BY 
                p.id
            ORDER BY 
                quantity_sold DESC
            LIMIT ?
        ''', (start_date, limit))
        
        products = [dict(row) for row in cursor.fetchall()]
        
        # Calculate trend percentage (comparing to previous period)
        for product in products:
            product_id = product['id']
            
            # Get sales for previous period
            previous_start = (datetime.now() - timedelta(days=days*2)).strftime('%Y-%m-%d')
            previous_end = start_date
            
            cursor.execute('''
                SELECT 
                    SUM(si.quantity) as prev_quantity
                FROM 
                    sale_items si
                    JOIN sales s ON si.sale_id = s.id
                WHERE 
                    si.product_id = ?
                    AND s.sale_date >= ?
                    AND s.sale_date < ?
                    AND (s.is_deleted IS NULL OR s.is_deleted = 0)
            ''', (product_id, previous_start, previous_end))
            
            prev_result = cursor.fetchone()
            prev_quantity = prev_result['prev_quantity'] if prev_result and prev_result['prev_quantity'] else 0
            
            # Calculate trend
            current_quantity = product['quantity_sold']
            if prev_quantity > 0:
                trend_percent = ((current_quantity - prev_quantity) / prev_quantity) * 100
            else:
                trend_percent = 100  # If no previous sales, consider it 100% growth
            
            product['trend'] = round(trend_percent, 1)
        
        conn.close()
        return products
    
    def get_sales_chart_data(self, days=7):
        """Get daily sales data for chart"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get daily data
        daily_data = []
        daily_labels = []
        
        for i in range(days-1, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_labels.append((datetime.now() - timedelta(days=i)).strftime('%d/%m'))
            
            cursor.execute('''
                SELECT COALESCE(SUM(total_amount), 0) as daily_total
                FROM sales
                WHERE DATE(sale_date) = ? AND (is_deleted IS NULL OR is_deleted = 0)
            ''', (date,))
            
            result = cursor.fetchone()
            daily_total = result['daily_total'] if result else 0
            daily_data.append(daily_total)
        
        # Get weekly data
        weekly_data = []
        weekly_labels = []
        
        for i in range(4, 0, -1):
            week_end = datetime.now() - timedelta(days=(i-1)*7)
            week_start = week_end - timedelta(days=6)
            
            week_label = f"{week_start.strftime('%d/%m')}-{week_end.strftime('%d/%m')}"
            weekly_labels.append(week_label)
            
            cursor.execute('''
                SELECT COALESCE(SUM(total_amount), 0) as weekly_total
                FROM sales
                WHERE sale_date BETWEEN ? AND ? AND (is_deleted IS NULL OR is_deleted = 0)
            ''', (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
            
            result = cursor.fetchone()
            weekly_total = result['weekly_total'] if result else 0
            weekly_data.append(weekly_total)
        
        conn.close()
        return {
            'daily': {
                'labels': daily_labels,
                'data': daily_data
            },
            'weekly': {
                'labels': weekly_labels,
                'data': weekly_data
            }
        }
    
    def add_to_sync_queue(self, table_name, record_id, operation, data=None):
        """Add operation to sync queue for offline functionality"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sync_queue (table_name, record_id, operation, data)
            VALUES (?, ?, ?, ?)
        ''', (table_name, record_id, operation, json.dumps(data) if data else None))
        conn.commit()
        conn.close()
    
    def get_pending_sync_operations(self):
        """Get pending sync operations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM sync_queue WHERE sync_status = 'pending'
            ORDER BY created_at ASC
        ''')
        operations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return operations
    
    def mark_sync_completed(self, sync_id):
        """Mark sync operation as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE sync_queue SET sync_status = 'synced', synced_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (sync_id,))
        conn.commit()
        conn.close()
        
    def get_customers_list(self):
        """Get list of active customers"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if dedicated customers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
        has_table = cursor.fetchone() is not None

        if has_table:
            cursor.execute('''
                SELECT id, name, phone
                FROM customers
                WHERE is_active = 1
                ORDER BY id
            ''')
        else:
            # Fallback: derive customers from sales table
            cursor.execute('''
                SELECT MIN(rowid) as id, customer_name as name, customer_phone as phone
                FROM sales
                WHERE customer_name != ''
                GROUP BY customer_name, customer_phone
                ORDER BY customer_name
            ''')
        
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return customers

    def create_customer(self, name, phone='', email='', address=''):
        """Create a new customer record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customers (name, phone, email, address)
            VALUES (?, ?, ?, ?)
        ''', (name, phone, email, address))
        customer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return customer_id
    
    def get_customer_by_id(self, customer_id):
        """Get a customer by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, phone, email, address, created_at, updated_at
            FROM customers
            WHERE id = ? AND is_active = 1
        ''', (customer_id,))
        customer = cursor.fetchone()
        conn.close()
        return dict(customer) if customer else None
    
    def update_customer(self, customer_id, name, phone='', email='', address=''):
        """Update an existing customer record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE customers
            SET name = ?, phone = ?, email = ?, address = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND is_active = 1
        ''', (name, phone, email, address, customer_id))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0
    
    def delete_customer(self, customer_id):
        """Soft delete a customer (mark as inactive)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE customers
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND is_active = 1
        ''', (customer_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0
        
    def get_sales_stats(self):
        """Get statistics for sales dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Today's sales - explicitly using current date to avoid timezone issues
        today_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as amount
            FROM sales
            WHERE DATE(sale_date) = ? AND (is_deleted IS NULL OR is_deleted = 0)
        ''', (today_date,))
        today = cursor.fetchone()
        
        # This month's sales - using current year and month
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as amount
            FROM sales
            WHERE strftime('%Y-%m', sale_date) = ? AND (is_deleted IS NULL OR is_deleted = 0)
        ''', (current_month,))
        month = cursor.fetchone()
        
        # Credit sales
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(remaining_amount), 0) as amount
            FROM client_debts
            WHERE status = 'pending'
        ''')
        credits = cursor.fetchone()
        
        conn.close()
        
        return {
            'today': dict(today),
            'month': dict(month),
            'credits': dict(credits)
        }

    def backup_database(self):
        """Create a backup of the database"""
        try:
            backup_dir = os.path.join(os.path.dirname(self.db_path), '..', 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'quincaillerie_backup_{timestamp}.db')
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            raise