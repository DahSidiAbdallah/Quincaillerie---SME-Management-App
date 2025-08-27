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


# Get the application directory
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        logger.info(f"Connecting to database at: {self.db_path}")
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

            # Generic app settings key/value store for flexible configuration
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
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
                    selling_price REAL NOT NULL,
                    sku TEXT,
                    barcode TEXT,
                    category TEXT,
                    supplier TEXT,
                    initial_stock INTEGER DEFAULT 0,
                    current_stock INTEGER DEFAULT 0,
                    reorder_level INTEGER DEFAULT 5,
                    min_order_quantity INTEGER DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    image_url TEXT
                )
            ''')

            # Add index for product lookups (split statements to avoid sqlite3 single-statement restriction)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)')
            
            # Stock Movements table (for inventory tracking)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    movement_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    reference_id INTEGER,
                    reference_type TEXT,
                    notes TEXT,
                    movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Sales table (Phase 1.3) - add status and credit_due_date columns if not exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT,
                    customer_id INTEGER,
                    customer_name TEXT,
                    customer_phone TEXT,
                    total_amount REAL NOT NULL,
                    paid_amount REAL NOT NULL,
                    payment_method TEXT DEFAULT 'cash',
                    is_credit BOOLEAN DEFAULT 0,
                    credit_due_date TEXT,
                    status TEXT DEFAULT 'paid',
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    notes TEXT,
                    is_deleted BOOLEAN DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            ''')

            # --- MIGRATION: Add missing columns if not present ---
            cursor.execute('PRAGMA table_info(sales)')
            sales_cols = [col[1] for col in cursor.fetchall()]
            if 'status' not in sales_cols:
                cursor.execute("ALTER TABLE sales ADD COLUMN status TEXT DEFAULT 'paid'")
            if 'credit_due_date' not in sales_cols:
                cursor.execute("ALTER TABLE sales ADD COLUMN credit_due_date TEXT")
            if 'is_credit' not in sales_cols:
                cursor.execute("ALTER TABLE sales ADD COLUMN is_credit BOOLEAN DEFAULT 0")
            if 'paid_amount' not in sales_cols and 'amount_paid' in sales_cols:
                cursor.execute("ALTER TABLE sales ADD COLUMN paid_amount REAL DEFAULT 0")
                cursor.execute("UPDATE sales SET paid_amount = amount_paid")
            if 'customer_name' not in sales_cols:
                cursor.execute("ALTER TABLE sales ADD COLUMN customer_name TEXT")
            if 'customer_phone' not in sales_cols:
                cursor.execute("ALTER TABLE sales ADD COLUMN customer_phone TEXT")
            if 'updated_at' not in sales_cols:
                cursor.execute("ALTER TABLE sales ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

            # Sale details table (for items in each sale)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    discount_percent REAL DEFAULT 0,
                    total_price REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')

            # Add index for sale details lookups (split to avoid sqlite single-statement restriction)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_details_sale_id ON sale_details(sale_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_details_product_id ON sale_details(product_id)')
            
            # Payments table (for tracking partial payments)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT DEFAULT 'cash',
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    created_by INTEGER,
                    FOREIGN KEY (sale_id) REFERENCES sales (id)
                )
            ''')
            
            # Expenses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT,
                    expense_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    notes TEXT,
                    is_deleted BOOLEAN DEFAULT 0
                )
            ''')
            
            # Settings table for app configuration
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
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
            
            # Check if settings exist, add if not
            cursor.execute("SELECT COUNT(*) FROM settings")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO settings (
                        store_name, 
                        store_address, 
                        store_phone, 
                        tax_rate, 
                        currency, 
                        language, 
                        low_stock_threshold, 
                        ai_features_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'Quincaillerie',
                    'Nouakchott, Mauritanie',
                    '+222 45 12 34 56',
                    0.0,
                    'MRU',
                    'fr',
                    5,
                    1
                ))
            
            # User activity log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    description TEXT,
                    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create a default admin user if none exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
            if cursor.fetchone()[0] == 0:
                default_pin = '1234'  # Default PIN for initial setup
                pin_hash = generate_password_hash(default_pin)
                cursor.execute('''
                    INSERT INTO users (username, pin_hash, role, language)
                    VALUES (?, ?, ?, ?)
                ''', ('admin', pin_hash, 'admin', 'fr'))
                
                # Log the default user creation
                logger.info("Created default admin user with PIN 1234")
            
            # Commit all changes
            conn.commit()
            
            logger.info("Database initialization completed successfully")
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error initializing database: {e}")
            return False
        finally:
            conn.close()
    
    def authenticate_user(self, username, pin):
        """Authenticate a user with username and PIN"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, pin_hash, role, language
                FROM users
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            user = cursor.fetchone()
            
            if user and check_password_hash(user['pin_hash'], pin):
                # Update last login time
                cursor.execute('''
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user['id'],))
                
                conn.commit()
                
                # Return user info as dict
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'language': user['language']
                }
            
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
        finally:
            conn.close()
    
    def get_users(self):
        """Get all users for admin panel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, role, language, created_at, last_login, is_active
                FROM users
                ORDER BY username
            ''')
            
            users = []
            for row in cursor.fetchall():
                user = dict(row)
                
                # Format dates
                for key in ['created_at', 'last_login']:
                    if key in user and user[key]:
                        try:
                            date_obj = datetime.fromisoformat(user[key].replace('Z', '+00:00'))
                            user[f'{key}_formatted'] = date_obj.strftime('%d/%m/%Y %H:%M')
                        except Exception:
                            user[f'{key}_formatted'] = user[key]
                
                users.append(user)
            
            return users
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []
        finally:
            conn.close()
    
    def create_user(self, user_data):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            username = user_data.get('username')
            pin = user_data.get('pin')
            role = user_data.get('role', 'employee')
            language = user_data.get('language', 'fr')
            
            # Check if username exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return {'success': False, 'error': 'Ce nom d\'utilisateur existe déjà'}
            
            # Hash PIN
            pin_hash = generate_password_hash(pin)
            
            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, pin_hash, role, language)
                VALUES (?, ?, ?, ?)
            ''', (username, pin_hash, role, language))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return {'success': True, 'user_id': user_id}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating user: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def update_user(self, user_id, user_data):
        """Update an existing user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            # Only update fields that are provided
            if 'username' in user_data:
                # Check if username is already taken by a different user
                cursor.execute('SELECT id FROM users WHERE username = ? AND id != ?', 
                               (user_data['username'], user_id))
                if cursor.fetchone():
                    return {'success': False, 'error': 'Ce nom d\'utilisateur existe déjà'}
                
                updates.append('username = ?')
                params.append(user_data['username'])
            
            if 'pin' in user_data and user_data['pin']:
                # Hash new PIN
                pin_hash = generate_password_hash(user_data['pin'])
                updates.append('pin_hash = ?')
                params.append(pin_hash)
            
            if 'role' in user_data:
                updates.append('role = ?')
                params.append(user_data['role'])
            
            if 'language' in user_data:
                updates.append('language = ?')
                params.append(user_data['language'])
            
            if 'is_active' in user_data:
                updates.append('is_active = ?')
                params.append(1 if user_data['is_active'] else 0)
            
            if not updates:
                return {'success': True, 'message': 'Aucune modification'}
            
            # Build update query
            query = f'''
                UPDATE users
                SET {', '.join(updates)}
                WHERE id = ?
            '''
            
            params.append(user_id)
            cursor.execute(query, params)
            
            if cursor.rowcount == 0:
                return {'success': False, 'error': 'Utilisateur non trouvé'}
            
            conn.commit()
            return {'success': True}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating user: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def delete_user(self, user_id):
        """Delete a user (soft delete by setting is_active=0)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if this is the only admin
            cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin" AND is_active = 1')
            admin_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'error': 'Utilisateur non trouvé'}
            
            if user['role'] == 'admin' and admin_count <= 1:
                return {'success': False, 'error': 'Impossible de supprimer le seul administrateur'}
            
            # Soft delete the user
            cursor.execute('''
                UPDATE users
                SET is_active = 0
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            return {'success': True}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting user: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def log_user_action(self, user_id, action_type, description):
        """Log user activity, respecting audit logging toggle (app_settings.audit_log_enabled)."""
        # Quick check for audit logging enabled (defaults to True)
        try:
            if not self.is_audit_enabled():
                return True
        except Exception:
            # If we fail to determine, proceed with logging to be safe
            pass

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''
                INSERT INTO user_activity_log (user_id, action_type, description)
                VALUES (?, ?, ?)
                ''',
                (user_id, action_type, description),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging user action: {e}")
            return False
        finally:
            conn.close()

    def is_audit_enabled(self) -> bool:
        """Return True if audit logging is enabled in app_settings (default True)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM app_settings WHERE key = 'audit_log_enabled'")
            row = cursor.fetchone()
            if not row:
                return True
            val = row['value'] if isinstance(row, sqlite3.Row) else row[0]
            if isinstance(val, str):
                val_lower = val.strip().lower()
                if val_lower in ('true', '1', 'yes', 'on'):
                    return True
                if val_lower in ('false', '0', 'no', 'off'):
                    return False
            # Try JSON bool
            try:
                decoded = json.loads(val)
                if isinstance(decoded, bool):
                    return decoded
            except Exception:
                pass
            return bool(val)
        except Exception:
            return True
        finally:
            conn.close()

    def upsert_user_by_username(self, user_data: dict):
        """Upsert a user by username. If exists, update fields; else create a new user.
        Expects keys: username (required), role, language, is_active, pin (optional for new users).
        Returns dict(success: bool, user_id?: int, created?: bool)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            username = user_data.get('username')
            if not username:
                return {'success': False, 'error': 'username manquant'}
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            if row:
                user_id = row['id'] if isinstance(row, sqlite3.Row) else row[0]
                updates = []
                params = []
                for key in ('role', 'language', 'is_active'):
                    if key in user_data:
                        updates.append(f"{key} = ?")
                        val = user_data[key]
                        if key == 'is_active':
                            val = 1 if val in (True, 1, '1', 'true', 'True') else 0
                        params.append(val)
                if updates:
                    params.append(user_id)
                    cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
                conn.commit()
                return {'success': True, 'user_id': user_id, 'created': False}
            else:
                # Create
                pin = user_data.get('pin') or '1234'
                pin_hash = generate_password_hash(pin)
                role = user_data.get('role', 'employee')
                language = user_data.get('language', 'fr')
                cursor.execute(
                    'INSERT INTO users (username, pin_hash, role, language) VALUES (?, ?, ?, ?)',
                    (username, pin_hash, role, language),
                )
                user_id = cursor.lastrowid
                conn.commit()
                return {'success': True, 'user_id': user_id, 'created': True}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error upserting user by username: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_recent_activities(self, limit=20):
        """Get recent user activities for dashboard. Supports action_time or created_at."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            def fetch(col_name: str):
                try:
                    cursor.execute(
                        f'''
                        SELECT 
                            a.id, a.action_type, a.description, a.{col_name} AS created_at,
                            u.username
                        FROM user_activity_log a
                        JOIN users u ON a.user_id = u.id
                        ORDER BY a.{col_name} DESC
                        LIMIT ?
                        ''',
                        (limit,),
                    )
                    return cursor.fetchall()
                except Exception:
                    return []

            rows = fetch('action_time')
            if not rows:
                rows = fetch('created_at')

            activities = []
            for row in rows:
                activity = dict(row)
                # Format date
                if 'created_at' in activity and activity['created_at']:
                    try:
                        action_time = datetime.fromisoformat(str(activity['created_at']).replace('Z', '+00:00'))
                        activity['formatted_time'] = action_time.strftime('%d/%m/%Y %H:%M')
                    except Exception:
                        activity['formatted_time'] = activity.get('created_at')
                activities.append(activity)

            return activities
        except Exception as e:
            logger.error(f"Error fetching recent activities: {e}")
            return []
        finally:
            conn.close()
    
    def get_inventory_stats(self):
        """Get inventory statistics for dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN current_stock <= reorder_level THEN 1 ELSE 0 END) as low_stock,
                    SUM(CASE WHEN current_stock = 0 THEN 1 ELSE 0 END) as out_of_stock,
                    SUM(current_stock) as total_items,
                    SUM(current_stock * purchase_price) as inventory_value
                FROM products
                WHERE is_active = 1
            ''')
            
            stats = dict(cursor.fetchone())
            
            # Get category breakdown
            cursor.execute('''
                SELECT 
                    category,
                    COUNT(*) as count
                FROM products
                WHERE is_active = 1
                GROUP BY category
                ORDER BY count DESC
            ''')
            
            categories = []
            for row in cursor.fetchall():
                categories.append(dict(row))
            
            stats['categories'] = categories
            
            return stats
        except Exception as e:
            logger.error(f"Error fetching inventory stats: {e}")
            return {
                'total': 0,
                'low_stock': 0,
                'out_of_stock': 0,
                'total_items': 0,
                'inventory_value': 0,
                'categories': []
            }
        finally:
            conn.close()
    
    def get_low_stock_items(self, limit=5):
        """Get low stock items for dashboard alerts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    id, name, sku, category, current_stock, reorder_level
                FROM products
                WHERE is_active = 1 AND current_stock <= reorder_level
                ORDER BY (current_stock * 1.0 / reorder_level)
                LIMIT ?
            ''', (limit,))
            
            items = []
            for row in cursor.fetchall():
                items.append(dict(row))
            
            return items
        except Exception as e:
            logger.error(f"Error fetching low stock items: {e}")
            return []
        finally:
            conn.close()
    
    def get_today_sales(self):
        """Get today's sales summary for dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT 
                    SUM(total_amount) as total,
                    COUNT(*) as count
                FROM sales
                WHERE DATE(sale_date) = ?
                AND is_deleted = 0
            ''', (today,))
            
            result = cursor.fetchone()
            
            return {
                'total': float(result['total']) if result and result['total'] else 0,
                'count': result['count'] if result else 0
            }
        except Exception as e:
            logger.error(f"Error fetching today's sales: {e}")
            return {'total': 0, 'count': 0}
        finally:
            conn.close()
    
    def get_total_revenue(self):
        """Get total revenue for dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT SUM(total_amount) as total
                FROM sales
                WHERE is_deleted = 0
            ''')
            
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0
        except Exception as e:
            logger.error(f"Error fetching total revenue: {e}")
            return 0
        finally:
            conn.close()
    
    def get_sales_stats(self):
        """Get sales statistics for dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Today's sales
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT 
                    SUM(total_amount) as amount,
                    COUNT(*) as count
                FROM sales
                WHERE DATE(sale_date) = ?
                AND is_deleted = 0
            ''', (today,))
            today_result = cursor.fetchone()
            
            # This month's sales
            this_month = datetime.now().strftime('%Y-%m')
            cursor.execute('''
                SELECT 
                    SUM(total_amount) as amount,
                    COUNT(*) as count
                FROM sales
                WHERE strftime('%Y-%m', sale_date) = ?
                AND is_deleted = 0
            ''', (this_month,))
            month_result = cursor.fetchone()
            
            # Credit/partial sales (pending debts) - support DBs without remaining_amount and with legacy paid column name
            cursor.execute('PRAGMA table_info(sales)')
            sales_cols = [col[1] for col in cursor.fetchall()]
            if 'remaining_amount' in sales_cols:
                cursor.execute(
                    '''
                    SELECT 
                        SUM(remaining_amount) as amount,
                        COUNT(*) as count
                    FROM sales
                    WHERE remaining_amount > 0
                    AND is_deleted = 0
                    '''
                )
            else:
                # Derive remaining as total_amount - paid_column (amount_paid or paid_amount), with robust fallback
                tried = False
                for paid_col in ('amount_paid', 'paid_amount'):
                    if paid_col in sales_cols:
                        try:
                            tried = True
                            cursor.execute(
                                f'''
                                SELECT 
                                    SUM(total_amount - {paid_col}) as amount,
                                    SUM(CASE WHEN total_amount > {paid_col} THEN 1 ELSE 0 END) as count
                                FROM sales
                                WHERE (total_amount - {paid_col}) > 0
                                AND is_deleted = 0
                                '''
                            )
                            break
                        except Exception:
                            # Try next column name
                            continue
                if not tried:
                    # Fallback: no paid column, return zeros
                    return {
                        'today': {
                            'amount': float(today_result['amount']) if today_result and today_result['amount'] else 0,
                            'count': today_result['count'] if today_result else 0
                        },
                        'month': {
                            'amount': float(month_result['amount']) if month_result and month_result['amount'] else 0,
                            'count': month_result['count'] if month_result else 0
                        },
                        'credits': {
                            'amount': 0,
                            'count': 0
                        }
                    }
            credits_result = cursor.fetchone()
            
            return {
                'today': {
                    'amount': float(today_result['amount']) if today_result and today_result['amount'] else 0,
                    'count': today_result['count'] if today_result else 0
                },
                'month': {
                    'amount': float(month_result['amount']) if month_result and month_result['amount'] else 0,
                    'count': month_result['count'] if month_result else 0
                },
                'credits': {
                    'amount': float(credits_result['amount']) if credits_result and credits_result['amount'] else 0,
                    'count': credits_result['count'] if credits_result else 0
                }
            }
        except Exception as e:
            logger.error(f"Error fetching sales stats: {e}")
            return {
                'today': {'amount': 0, 'count': 0},
                'month': {'amount': 0, 'count': 0},
                'credits': {'amount': 0, 'count': 0}
            }
        finally:
            conn.close()
    
    def get_total_products(self):
        """Get total number of products"""
        return self.get_inventory_stats().get('total', 0)

    def get_customers_list(self):
        """Get list of active customers. Falls back to deriving from sales if needed."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            has_customers = cursor.fetchone() is not None
            if has_customers:
                cursor.execute(
                    '''
                    SELECT id, name, phone
                    FROM customers
                    WHERE is_active = 1
                    ORDER BY name
                    '''
                )
            else:
                # Fallback: derive basic customer list from sales if columns available
                # Attempt typical alternate columns customer_name/customer_phone
                try:
                    cursor.execute(
                        '''
                        SELECT MIN(rowid) as id, customer_name as name, customer_phone as phone
                        FROM sales
                        WHERE COALESCE(customer_name, '') <> ''
                        GROUP BY customer_name, customer_phone
                        ORDER BY customer_name
                        '''
                    )
                except Exception:
                    return []
            return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching customers list: {e}")
            return []
        finally:
            conn.close()

    def get_customer_by_id(self, customer_id: int):
        """Fetch a single customer by id if exists and active."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            if cursor.fetchone() is None:
                return None
            cursor.execute(
                '''
                SELECT id, name, phone, email, address, created_at, updated_at
                FROM customers
                WHERE id = ? AND is_active = 1
                ''',
                (customer_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching customer by id: {e}")
            return None
        finally:
            conn.close()

    def update_customer(self, customer_id: int, name: str, phone: str = '', email: str = '', address: str = ''):
        """Update basic customer fields if table exists."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                '''
                UPDATE customers
                SET name = ?, phone = ?, email = ?, address = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
                ''',
                (name, phone, email, address, customer_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating customer: {e}")
            return False
        finally:
            conn.close()

    def delete_customer(self, customer_id: int):
        """Soft-delete a customer if table exists."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                '''
                UPDATE customers
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
                ''',
                (customer_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting customer: {e}")
            return False
        finally:
            conn.close()

    def create_customer(self, name: str, phone: str = '', email: str = '', address: str = ''):
        """Create a new customer record if table exists; otherwise return None."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            if cursor.fetchone() is None:
                return None
            cursor.execute(
                '''
                INSERT INTO customers (name, phone, email, address)
                VALUES (?, ?, ?, ?)
                ''',
                (name, phone, email, address),
            )
            customer_id = cursor.lastrowid
            conn.commit()
            return customer_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating customer: {e}")
            return None
        finally:
            conn.close()
    
    def get_pending_debts(self):
        """Get pending client debts for dashboard (use client_debts table for consistency)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT SUM(remaining_amount) as total, COUNT(*) as count
                FROM client_debts
                WHERE remaining_amount > 0 AND status = 'pending'
            ''')
            result = cursor.fetchone()
            return {
                'total': float(result['total']) if result and result['total'] else 0,
                'count': result['count'] if result else 0
            }
        except Exception as e:
            logger.error(f"Error fetching pending debts: {e}")
            return {'total': 0, 'count': 0}
        finally:
            conn.close()

    def get_overdue_debts(self):
        """Get overdue client debts (remaining_amount > 0 and due_date before today).
        Uses client_debts table when available. Returns dict with 'total' and 'count'.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Defensive: ensure column names exist; most installs have due_date and remaining_amount
            cursor.execute("PRAGMA table_info(client_debts)")
            cols = [c[1] for c in cursor.fetchall()]
            if 'due_date' in cols and 'remaining_amount' in cols:
                cursor.execute('''
                    SELECT SUM(remaining_amount) as total, COUNT(*) as count
                    FROM client_debts
                    WHERE remaining_amount > 0 AND due_date IS NOT NULL AND DATE(due_date) < DATE('now')
                ''')
            else:
                # Fallback: if client_debts table or columns missing, return zeros
                return {'total': 0, 'count': 0}

            result = cursor.fetchone()
            return {
                'total': float(result['total']) if result and result['total'] else 0,
                'count': result['count'] if result else 0
            }
        except Exception as e:
            logger.error(f"Error fetching overdue debts: {e}")
            return {'total': 0, 'count': 0}
        finally:
            conn.close()

    def add_to_sync_queue(self, table_name, record_id, operation, data=None):
        """Add operation to a local sync queue (offline-first). Safe no-op if table doesn't exist.
        Table schema (created on first use):
          sync_queue(id PK, table_name TEXT, record_id INTEGER, operation TEXT,
                     data TEXT, sync_status TEXT DEFAULT 'pending',
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     synced_at TIMESTAMP)
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Ensure table exists (lazy create)
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER,
                    operation TEXT NOT NULL,
                    data TEXT,
                    sync_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_at TIMESTAMP
                )
                '''
            )
            payload = json.dumps(data) if data is not None else None
            cursor.execute(
                '''
                INSERT INTO sync_queue (table_name, record_id, operation, data)
                VALUES (?, ?, ?, ?)
                ''',
                (table_name, record_id, operation, payload),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.warning(f"add_to_sync_queue failed (non-fatal): {e}")
            return False
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def populate_mauritania_data(self):
        """Populate the database with minimal realistic sample data for Mauritania.
        This method is used by helper scripts to seed demo data and is safe to call multiple times.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Ensure at least one admin user exists
            cursor.execute("SELECT COUNT(*) as cnt FROM users")
            if cursor.fetchone()[0] == 0:
                pin_hash = generate_password_hash('1234')
                cursor.execute(
                    "INSERT INTO users (username, pin_hash, role, language) VALUES (?, ?, ?, ?)",
                    ('admin', pin_hash, 'admin', 'fr')
                )

            # Seed products if empty
            cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE is_active = 1")
            if cursor.fetchone()[0] == 0:
                sample_products = [
                    ('Marteau Acier', 'Marteau robuste pour usage général', 150.0, 220.0, 'OUTILS', 'Fournisseur A', '0012345678901', 50, 5),
                    ('Tournevis Plat', 'Tournevis plat 5mm', 80.0, 120.0, 'OUTILS', 'Fournisseur B', '0012345678902', 80, 8),
                    ('Peinture Blanche 5L', 'Peinture acrylique', 600.0, 900.0, 'PEINTURE', 'Fournisseur C', '0012345678903', 30, 4),
                    ('Clé à Molette', 'Clé ajustable 200mm', 200.0, 300.0, 'QUINCAILLERIE', 'Fournisseur A', '0012345678904', 40, 6),
                    ('Perceuse Électrique', 'Perceuse 500W', 1500.0, 2200.0, 'OUTILS', 'Fournisseur D', '0012345678905', 15, 3)
                ]
                for p in sample_products:
                    cursor.execute(
                        '''INSERT INTO products (name, description, purchase_price, selling_price, sku, barcode, category, supplier, initial_stock, current_stock, reorder_level)
                           VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)''',
                        (p[0], p[1], p[2], p[3], p[6], p[4], p[5], p[7], p[7], p[8])
                    )

            # Seed a few sales if none
            cursor.execute("SELECT COUNT(*) FROM sales WHERE is_deleted = 0")
            has_sales = cursor.fetchone()[0] > 0
            if not has_sales:
                # Get product ids and prices
                cursor.execute("SELECT id, selling_price FROM products WHERE is_active = 1")
                products = cursor.fetchall()
                if products:
                    from random import randint, choice
                    for d in range(10):
                        sale_date = (datetime.now() - timedelta(days=randint(0, 9))).strftime('%Y-%m-%d %H:%M:%S')
                        payment_method = choice(['cash', 'mobile', 'cash', 'cash'])
                        items_count = randint(1, 3)
                        total_amount = 0.0
                        cursor.execute('''
                            INSERT INTO sales (invoice_number, customer_id, total_amount, amount_paid, remaining_amount, payment_method, payment_status, sale_date, created_by, notes, is_deleted)
                            VALUES (?, NULL, 0, 0, 0, ?, 'paid', ?, 1, NULL, 0)
                        ''', (f'INV{int(datetime.now().timestamp())}{d}', payment_method, sale_date))
                        sale_id = cursor.lastrowid
                        for _ in range(items_count):
                            pr = choice(products)
                            product_id = pr['id']
                            unit_price = float(pr['selling_price'])
                            qty = randint(1, 4)
                            line_total = unit_price * qty
                            total_amount += line_total
                            cursor.execute('''
                                INSERT INTO sale_details (sale_id, product_id, quantity, unit_price, discount_percent, total_price)
                                VALUES (?, ?, ?, ?, 0, ?)
                            ''', (sale_id, product_id, qty, unit_price, line_total))
                            # Decrease stock and log movement
                            cursor.execute("UPDATE products SET current_stock = current_stock - ? WHERE id = ?", (qty, product_id))
                            cursor.execute('''
                                INSERT INTO stock_movements (product_id, movement_type, quantity, reference_id, reference_type, notes, created_by)
                                VALUES (?, 'sale', ?, ?, 'sale', NULL, 1)
                            ''', (product_id, qty, sale_id))
                        # finalize sale totals
                        cursor.execute("UPDATE sales SET total_amount = ?, amount_paid = ?, remaining_amount = 0 WHERE id = ?", (total_amount, total_amount, sale_id))

            # Seed recent activities if none
            cursor.execute("SELECT COUNT(*) FROM user_activity_log")
            has_activities = cursor.fetchone()[0] > 0
            if not has_activities:
                samples = [
                    ('sale', 'Vente réalisée au comptoir'),
                    ('stock', 'Sortie de stock pour commande client'),
                    ('login', 'Connexion administrateur'),
                    ('payment', 'Paiement reçu en espèces'),
                    ('stock', 'Réception de marchandises (entrée)')
                ]
                # Find an admin user id
                cursor.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
                admin_row = cursor.fetchone()
                admin_id = admin_row['id'] if admin_row else 1
                for action_type, description in samples:
                    cursor.execute(
                        """
                        INSERT INTO user_activity_log (user_id, action_type, description, action_time)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (admin_id, action_type, description)
                    )

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to populate Mauritania data: {e}")
            return False
        finally:
            conn.close()
    
    def get_cash_balance(self):
        """Get cash balance (income - expenses)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get total sales income
            cursor.execute('''
                SELECT SUM(total_amount) as total
                FROM sales
                WHERE is_deleted = 0
            ''')
            
            sales_result = cursor.fetchone()
            total_sales = float(sales_result['total']) if sales_result and sales_result['total'] else 0
            
            # Get total expenses - check if is_deleted column exists first
            cursor.execute('PRAGMA table_info(expenses)')
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'is_deleted' in columns:
                cursor.execute('''
                    SELECT SUM(amount) as total
                    FROM expenses
                    WHERE is_deleted = 0
                ''')
            else:
                # Use without is_deleted filter if column doesn't exist
                cursor.execute('''
                    SELECT SUM(amount) as total
                    FROM expenses
                ''')
            
            expenses_result = cursor.fetchone()
            total_expenses = float(expenses_result['total']) if expenses_result and expenses_result['total'] else 0
            
            # Calculate balance
            return total_sales - total_expenses
        except Exception as e:
            logger.error(f"Error calculating cash balance: {e}")
            return 0
        finally:
            conn.close()
    
    def get_top_selling_products(self, days=30, limit=5):
        """Get top selling products for dashboard.
        Prefer sale_items (new schema); gracefully fallback to sale_details if needed.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Calculate date range
            end_date = datetime.now()
            # Include today in the range
            start_date = end_date - timedelta(days=days - 1)

            # Detect which sale detail table to use
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sale_items'")
                has_sale_items = cursor.fetchone() is not None
            except Exception:
                has_sale_items = False

            table_alias = 'si' if has_sale_items else 'sd'
            table_name = 'sale_items' if has_sale_items else 'sale_details'

            query = f'''
                SELECT
                    p.id, p.name, p.category,
                    SUM({table_alias}.quantity) as quantity_sold,
                    SUM({table_alias}.total_price) as total_sales
                FROM {table_name} {table_alias}
                JOIN products p ON {table_alias}.product_id = p.id
                JOIN sales s ON {table_alias}.sale_id = s.id
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
                AND (CASE WHEN EXISTS (SELECT 1 FROM pragma_table_info('sales') WHERE name='is_deleted') THEN s.is_deleted = 0 ELSE 1 END)
                GROUP BY p.id
                ORDER BY quantity_sold DESC
                LIMIT ?
            '''

            cursor.execute(
                query,
                (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), limit),
            )

            products = [dict(row) for row in cursor.fetchall()]
            return products
        except Exception as e:
            logger.error(f"Error fetching top selling products: {e}")
            return []
        finally:
            conn.close()
    
    def get_sales_chart_data(self, days=7):
        """Get sales chart data for dashboard visualization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Calculate date range including today
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days - 1)
            
            # Daily sales data
            cursor.execute('''
                SELECT 
                    DATE(sale_date) as date,
                    SUM(total_amount) as total
                FROM sales
                WHERE sale_date BETWEEN ? AND ?
                AND is_deleted = 0
                GROUP BY DATE(sale_date)
                ORDER BY date
            ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            
            daily_data = {}
            for row in cursor.fetchall():
                daily_data[row['date']] = float(row['total'])
            
            # Create a complete dataset with all days in range
            daily_labels = []
            daily_values = []
            
            for i in range(days):
                date = (end_date - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
                label = (end_date - timedelta(days=days-i-1)).strftime('%d/%m')
                daily_labels.append(label)
                daily_values.append(daily_data.get(date, 0))
            
            # Weekly sales data (for longer trends)
            cursor.execute('''
                SELECT 
                    strftime('%Y-%W', sale_date) as week,
                    SUM(total_amount) as total
                FROM sales
                WHERE sale_date >= date(?, '-4 weeks')
                AND is_deleted = 0
                GROUP BY week
                ORDER BY week
            ''', (end_date.strftime('%Y-%m-%d'),))
            
            weekly_data = {}
            for row in cursor.fetchall():
                weekly_data[row['week']] = float(row['total'])
            
            # Create labels for weeks
            weekly_labels = []
            weekly_values = []
            
            for i in range(4):
                # Get the first day of each week
                week_start = end_date - timedelta(days=end_date.weekday() + 7*i)
                week_key = week_start.strftime('%Y-%W')
                week_label = f"{week_start.strftime('%d/%m')} - {(week_start + timedelta(days=6)).strftime('%d/%m')}"
                
                weekly_labels.insert(0, week_label)
                weekly_values.insert(0, weekly_data.get(week_key, 0))
            
            return {
                'daily': {
                    'labels': daily_labels,
                    'data': daily_values
                },
                'weekly': {
                    'labels': weekly_labels,
                    'data': weekly_values
                }
            }
        except Exception as e:
            logger.error(f"Error generating sales chart data: {e}")
            return {
                'daily': {'labels': [], 'data': []},
                'weekly': {'labels': [], 'data': []}
            }
        finally:
            conn.close()
    
    def get_app_settings(self):
        """Get application settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Base settings from row-based table
            cursor.execute('SELECT * FROM settings WHERE id = 1')
            settings_row = cursor.fetchone()
            base_settings = dict(settings_row) if settings_row else {
                'store_name': 'Quincaillerie',
                'store_address': '',
                'store_phone': '',
                'tax_rate': 0.0,
                'currency': 'MRU',
                'language': 'fr',
                'low_stock_threshold': 5,
                'ai_features_enabled': True
            }

            # Overlay with key-value app_settings for flexible keys
            try:
                cursor.execute('SELECT key, value FROM app_settings')
                for row in cursor.fetchall():
                    key = row['key'] if isinstance(row, sqlite3.Row) else row[0]
                    val = row['value'] if isinstance(row, sqlite3.Row) else row[1]
                    # Try to decode JSON values, else keep as string/bool/number
                    try:
                        decoded = json.loads(val)
                        base_settings[key] = decoded
                    except Exception:
                        # Coerce simple types
                        if val in ('true', 'false'):
                            base_settings[key] = val == 'true'
                        else:
                            # Try number
                            try:
                                if '.' in str(val):
                                    base_settings[key] = float(val)
                                else:
                                    base_settings[key] = int(val)
                            except Exception:
                                base_settings[key] = val
            except Exception:
                # app_settings may not exist; ignore
                pass

            # Ensure presence of security-related defaults so UI fields are populated
            if 'session_timeout_minutes' not in base_settings or not isinstance(base_settings.get('session_timeout_minutes'), (int, float)):
                base_settings['session_timeout_minutes'] = 30
            if 'max_login_attempts' not in base_settings or not isinstance(base_settings.get('max_login_attempts'), (int, float)):
                base_settings['max_login_attempts'] = 5
            if 'audit_log_enabled' not in base_settings or not isinstance(base_settings.get('audit_log_enabled'), bool):
                base_settings['audit_log_enabled'] = True

            return base_settings
        except Exception as e:
            logger.error(f"Error fetching app settings: {e}")
            return {}
        finally:
            conn.close()
    
    def set_app_settings(self, settings_data):
        """Update application settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Determine columns of settings table
            cursor.execute('PRAGMA table_info(settings)')
            settings_columns = [row[1] for row in cursor.fetchall()]

            # Split incoming dict into known settings columns and extra keys
            settings_updates = {}
            kv_updates = {}
            for key, value in settings_data.items():
                if key in ['id', 'updated_at']:
                    continue
                if key in settings_columns:
                    settings_updates[key] = value
                else:
                    kv_updates[key] = value

            # Upsert to settings table for known columns
            cursor.execute('SELECT 1 FROM settings WHERE id = 1')
            exists = cursor.fetchone() is not None
            if settings_updates:
                if exists:
                    updates = [f"{k} = ?" for k in settings_updates.keys()]
                    params = list(settings_updates.values())
                    updates.append('updated_at = CURRENT_TIMESTAMP')
                    cursor.execute(f"UPDATE settings SET {', '.join(updates)} WHERE id = 1", params)
                else:
                    keys = list(settings_updates.keys()) + ['id']
                    placeholders = ['?'] * len(settings_updates) + ['1']
                    params = list(settings_updates.values())
                    cursor.execute(
                        f"INSERT INTO settings ({', '.join(keys)}) VALUES ({', '.join(placeholders)})",
                        params
                    )

            # Upsert extra keys into app_settings (store JSON when needed)
            if kv_updates:
                for key, value in kv_updates.items():
                    to_store = value
                    if isinstance(value, (dict, list)):
                        to_store = json.dumps(value)
                    else:
                        to_store = str(value)
                    cursor.execute(
                        "REPLACE INTO app_settings (key, value) VALUES (?, ?)",
                        (key, to_store)
                    )
            
            conn.commit()
            return {'success': True}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating app settings: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def update_user_language(self, user_id, language):
        """Update the preferred language for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users SET language = ?, last_login = last_login
                WHERE id = ?
            ''', (language, user_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating user language: {e}")
            return False
        finally:
            conn.close()