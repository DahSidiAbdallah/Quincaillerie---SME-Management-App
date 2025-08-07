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

            # Add index for product lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
                CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
                CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
            ''')
            
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
            
            # Sales table (Phase 1.3)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT,
                    customer_id INTEGER,
                    total_amount REAL NOT NULL,
                    amount_paid REAL NOT NULL,
                    remaining_amount REAL DEFAULT 0,
                    payment_method TEXT DEFAULT 'cash',
                    payment_status TEXT DEFAULT 'paid',
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    notes TEXT,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            ''')

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

            # Add index for sale details lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sale_details_sale_id ON sale_details(sale_id);
                CREATE INDEX IF NOT EXISTS idx_sale_details_product_id ON sale_details(product_id);
            ''')
            
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
        """Log user activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_activity_log (user_id, action_type, description)
                VALUES (?, ?, ?)
            ''', (user_id, action_type, description))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging user action: {e}")
            return False
        finally:
            conn.close()
    
    def get_recent_activities(self, limit=20):
        """Get recent user activities for dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    a.id, a.action_type, a.description, a.created_at,
                    u.username
                FROM user_activity_log a
                JOIN users u ON a.user_id = u.id
                ORDER BY a.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            activities = []
            for row in cursor.fetchall():
                activity = dict(row)
                
                # Format date
                if 'created_at' in activity:
                    try:
                        action_time = datetime.fromisoformat(activity['created_at'].replace('Z', '+00:00'))
                        activity['formatted_time'] = action_time.strftime('%d/%m/%Y %H:%M')
                    except Exception:
                        activity['formatted_time'] = activity['action_time']
                
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
            
            # Credit sales (pending debts)
            cursor.execute('''
                SELECT 
                    SUM(total_amount - paid_amount) as amount,
                    COUNT(*) as count
                FROM sales
                WHERE (total_amount - paid_amount) > 0
                AND is_deleted = 0
            ''')
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
    
    def get_pending_debts(self):
        """Get pending credit sales for dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    SUM(total_amount - paid_amount) as total,
                    COUNT(*) as count
                FROM sales
                WHERE is_credit = 1 OR paid_amount < total_amount
                AND is_deleted = 0
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
        """Get top selling products for dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            cursor.execute('''
                SELECT 
                    p.id, p.name, p.category,
                    SUM(si.quantity) as quantity_sold,
                    SUM(si.total_price) as total_sales
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                JOIN sales s ON si.sale_id = s.id
                WHERE s.sale_date BETWEEN ? AND ?
                AND s.is_deleted = 0
                GROUP BY p.id
                ORDER BY quantity_sold DESC
                LIMIT ?
            ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), limit))
            
            products = []
            for row in cursor.fetchall():
                products.append(dict(row))
            
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
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
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
            cursor.execute('SELECT * FROM settings WHERE id = 1')
            settings = cursor.fetchone()
            
            if settings:
                return dict(settings)
            else:
                return {
                    'store_name': 'Quincaillerie',
                    'store_address': '',
                    'store_phone': '',
                    'tax_rate': 0.0,
                    'currency': 'MRU',
                    'language': 'fr',
                    'low_stock_threshold': 5,
                    'ai_features_enabled': True
                }
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
            # Get current settings
            cursor.execute('SELECT * FROM settings WHERE id = 1')
            current = cursor.fetchone()
            
            if current:
                # Update existing settings
                updates = []
                params = []
                
                for key, value in settings_data.items():
                    if key in ['id', 'updated_at']:  # Skip these fields
                        continue
                    
                    updates.append(f'{key} = ?')
                    params.append(value)
                
                if not updates:
                    return {'success': True, 'message': 'No changes made'}
                
                # Add updated_at and ID
                updates.append('updated_at = CURRENT_TIMESTAMP')
                
                # Build update query
                query = f'''
                    UPDATE settings
                    SET {', '.join(updates)}
                    WHERE id = 1
                '''
                
                cursor.execute(query, params)
            else:
                # Insert new settings
                keys = []
                placeholders = []
                params = []
                
                for key, value in settings_data.items():
                    if key in ['id', 'updated_at']:  # Skip these fields
                        continue
                    
                    keys.append(key)
                    placeholders.append('?')
                    params.append(value)
                
                # Add id = 1
                keys.append('id')
                placeholders.append('1')
                
                # Build insert query
                query = f'''
                    INSERT INTO settings ({', '.join(keys)})
                    VALUES ({', '.join(placeholders)})
                '''
                
                cursor.execute(query, params)
            
            conn.commit()
            return {'success': True}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating app settings: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()