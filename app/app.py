#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quincaillerie & SME Management App
Main Flask Application - Offline-First with AI Ready Architecture
Author: Dah Sidi Abdallah
Date: 2025-07-24
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import json
import sys

# Add the current directory to Python path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from datetime import datetime, timedelta
import uuid
from functools import wraps
import logging

# Import availability flag (actual imports occur in init block below)
MODULES_AVAILABLE = True

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'quincaillerie-app-2025-secure-key')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# Enable/disable debug and test pages via environment flag (default off)
app.config['DEBUG_PAGES'] = os.environ.get('DEBUG_PAGES', '0') in ('1', 'true', 'True')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database and other components with error handling
# Initialize globals first (to avoid 'possibly unbound' errors)
db_manager = None
stock_predictor = None
sales_forecaster = None
sync_manager = None
auth_bp = inventory_bp = sales_bp = customers_bp = finance_bp = reports_bp = ai_bp = dashboard_bp = settings_bp = admin_bp = None

if MODULES_AVAILABLE:
    try:
        # Initialize database manager first
        from db.database import DatabaseManager
        from api.auth import auth_bp
        from api.inventory import inventory_bp
        from api.sales import sales_bp
        from api.customers import customers_bp
        from api.admin import admin_bp
        from api.finance import finance_bp
        from api.reports import reports_bp
        from api.ai_insights import ai_bp
        from api.dashboard import dashboard_bp
        from api.settings import settings_bp, init_settings_routes
        from models.ml_forecasting import StockPredictor, SalesForecaster
        from offline.sync_manager import SyncManager
        from autologin import register_autologin_blueprint

        db_manager = DatabaseManager()
        db_manager.init_database()
        logger.info("Database initialized successfully")

        # Initialize AI models with proper error handling
        try:
            stock_predictor = StockPredictor()
            logger.info("Stock predictor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing stock predictor: {e}")
            stock_predictor = None

        try:
            sales_forecaster = SalesForecaster()
            logger.info("Sales forecaster initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing sales forecaster: {e}")
            sales_forecaster = None

        # Initialize sync manager for offline functionality
        try:
            sync_manager = SyncManager()
            logger.info("Sync manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing sync manager: {e}")
            sync_manager = None

        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
        app.register_blueprint(sales_bp, url_prefix='/api/sales')
        app.register_blueprint(customers_bp, url_prefix='/api')
        app.register_blueprint(finance_bp, url_prefix='/api/finance')
        app.register_blueprint(reports_bp, url_prefix='/api/reports')
        app.register_blueprint(ai_bp, url_prefix='/api/ai')
        app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')

        # Register auto-login blueprint
        register_autologin_blueprint(app)

        # Initialize settings routes with necessary dependencies (add English support)
        SUPPORTED_LANGUAGES = {'fr': 'Français', 'ar': 'العربية', 'en': 'English'}
        init_settings_routes(app, db_manager, MODULES_AVAILABLE, SUPPORTED_LANGUAGES)

        print("✅ All modules loaded successfully")
    except Exception as e:
        print(f"⚠️  Error initializing modules: {e}")
        MODULES_AVAILABLE = False
        # Make sure all components are defined even if initialization fails
        db_manager = None
        stock_predictor = None
        sales_forecaster = None
        sync_manager = None
else:
    print("📝 Running in minimal mode - some features may not be available")
    # Define components as None in minimal mode
    db_manager = None
    stock_predictor = None
    sales_forecaster = None
    sync_manager = None

# Language support
SUPPORTED_LANGUAGES = {
    'fr': 'Français',
    'ar': 'العربية',
    'en': 'English'
}

def get_user_language():
    """Get user's preferred language from session or default to French"""
    return session.get('language', 'fr')

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Accès administrateur requis', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_globals():
    """Inject global variables into all templates"""
    # Determine current currency from settings if possible
    current_currency = 'MRU'
    ai_enabled = True
    try:
        if db_manager is not None:
            settings = db_manager.get_app_settings()
            current_currency = (settings.get('currency') or 'MRU').upper()
            # Gate AI features with settings flag (default True if missing)
            ai_enabled = bool(settings.get('ai_features_enabled', True))
    except Exception as _e:
        current_currency = 'MRU'
        ai_enabled = True

    # Simple money formatter for templates
    def format_currency(value):
        try:
            num = float(value or 0)
            # French-style formatting: space thousands, comma decimals
            formatted = f"{num:,.2f}".replace(',', ' ').replace('.', ',')
            return f"{formatted} {current_currency}"
        except Exception:
            return f"0,00 {current_currency}"

    return {
        'current_language': get_user_language(),
        'supported_languages': SUPPORTED_LANGUAGES,
        'current_user': session.get('username', ''),
        'user_role': session.get('user_role', 'employee'),
        'app_version': '1.0.0',
        'current_year': datetime.now().year,
        'is_minimal_mode': not MODULES_AVAILABLE,
        'current_currency': current_currency,
    'format_currency': format_currency,
    'ai_features_enabled': ai_enabled
    }

# Main Routes
@app.route('/')
def index():
    """Main landing page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# PWA Routes
@app.route('/manifest.json')
def serve_manifest_file():
    """Serve the app manifest for PWA installation"""
    response = app.send_static_file('manifest.json')
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/sw.js')
def serve_service_worker_file():
    """Serve the service worker JavaScript file"""
    response = app.send_static_file('sw.js')
    # Set the correct content type to avoid MIME type errors
    response.headers['Content-Type'] = 'application/javascript'
    # Cache control - service worker should be checked frequently
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/api/health')
def health_check():
    """Health check endpoint for service worker"""
    try:
        # Check database connection
        if db_manager:
            db_manager.get_connection()
            return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})
        return jsonify({"status": "limited", "message": "Database not available", "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}), 500

@app.route('/offline')
def offline():
    """Offline page for PWA"""
    return render_template('offline.html')

@app.route('/offline-test')
def offline_test():
    """Test page for offline capabilities"""
    return render_template('offline_test.html')

@app.route('/admin/pwa')
def pwa_admin():
    """PWA administration page"""
    if 'user_id' not in session or session.get('is_admin') != True:
        flash('Vous devez être administrateur pour accéder à cette page.', 'error')
        return redirect(url_for('login'))
    return render_template('pwa_admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with PIN-based authentication"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        pin = data.get('pin')
        
        if not username or not pin:
            return jsonify({'success': False, 'message': 'Nom d\'utilisateur et PIN requis'})
        
        # Check credentials based on available modules
        if MODULES_AVAILABLE and db_manager is not None:
            user = db_manager.authenticate_user(username, pin)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_role'] = user['role']
                session['language'] = user.get('language', 'fr')
                
                # Log the login
                if db_manager is not None:
                    db_manager.log_user_action(user['id'], 'login', f'Connexion réussie pour {username}')
                
                if request.is_json:
                    return jsonify({'success': True, 'redirect': url_for('dashboard')})
                return redirect(url_for('dashboard'))
        else:
            # Fallback authentication for minimal mode
            if username == 'admin' and pin == '1234':
                session['user_id'] = 1
                session['username'] = 'admin'
                session['user_role'] = 'admin'
                session['language'] = 'fr'
                
                if request.is_json:
                    return jsonify({'success': True, 'redirect': url_for('dashboard')})
                return redirect(url_for('dashboard'))
        
        message = 'Nom d\'utilisateur ou PIN incorrect'
        if request.is_json:
            return jsonify({'success': False, 'message': message})
        flash(message, 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    if 'user_id' in session and db_manager is not None:
        try:
            db_manager.log_user_action(session['user_id'], 'logout', 'Déconnexion')
        except Exception as e:
            logger.error(f"Error logging logout action: {e}")
    session.clear()
    flash('Déconnexion réussie', 'success')
    return redirect(url_for('login'))

@app.route('/status')
@admin_required
def app_status():
    """Application status page for administrators"""
    modules_status = {
        'Database Manager': db_manager is not None,
        'Stock Predictor': stock_predictor is not None,
        'Sales Forecaster': sales_forecaster is not None,
        'Sync Manager': sync_manager is not None,
        'Auth API': auth_bp is not None,
        'Inventory API': inventory_bp is not None,
        'Sales API': sales_bp is not None,
        'Customers API': customers_bp is not None,
        'Finance API': finance_bp is not None,
        'Reports API': reports_bp is not None,
        'AI Insights API': ai_bp is not None,
        'Dashboard API': dashboard_bp is not None,
        'Settings API': settings_bp is not None,
        'Admin API': admin_bp is not None
    }
    
    system_info = {
        'Python Version': sys.version,
        'Running Mode': 'Full' if MODULES_AVAILABLE else 'Minimal',
        'Supported Languages': ', '.join(SUPPORTED_LANGUAGES.values()),
        'Default Language': SUPPORTED_LANGUAGES.get(get_user_language(), get_user_language())
    }
    
    return render_template('error.html', 
                          error_title="Application Status", 
                          error_message="Application Status and Configurations", 
                          modules_status=modules_status,
                          system_info=system_info,
                          is_status_page=True)

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - different views for admin vs employee"""
    user_role = session.get('user_role', 'employee')

    # Get dashboard data based on available modules
    if MODULES_AVAILABLE and db_manager is not None:
        try:
            # Fetch inventory statistics
            inv_stats = db_manager.get_inventory_stats()
            total_products = inv_stats.get('total', 0)
            low_stock_items = db_manager.get_low_stock_items() if db_manager is not None else []
            
            # Get today's sales summary
            today_sales_data = db_manager.get_today_sales() if db_manager is not None else {'total': 0, 'count': 0}
            today_sales = today_sales_data.get('total', 0) if today_sales_data else 0
            
            # Get revenue and financial data
            total_revenue = db_manager.get_total_revenue() if db_manager is not None else 0
            pending_debts = db_manager.get_pending_debts() if db_manager is not None else {'total': 0, 'count': 0}
            cash_balance = db_manager.get_cash_balance() if db_manager is not None else 0
            
            # Get activity log and top selling products
            recent_activities = db_manager.get_recent_activities(limit=10) if db_manager is not None else []
            top_selling_products = db_manager.get_top_selling_products(days=30, limit=5) if db_manager is not None else []
            # Broaden the window for first paint if recent window is empty
            if not top_selling_products and db_manager is not None:
                try:
                    top_selling_products = db_manager.get_top_selling_products(days=3650, limit=5)
                except Exception:
                    top_selling_products = []
            
            # Get sales chart data for visualization
            sales_chart_data = db_manager.get_sales_chart_data(days=7) if db_manager is not None else {'daily': {'labels': [], 'data': []}, 'weekly': {'labels': [], 'data': []}}
            
            # Compile the dashboard data
            dashboard_data = {
                'total_products': total_products,
                'low_stock_items': low_stock_items,
                'today_sales': today_sales,
                'total_revenue': total_revenue,
                'pending_debts': pending_debts,
                'cash_balance': cash_balance,
                'recent_activities': recent_activities,
                'top_selling_products': top_selling_products,
                'sales_chart_data': sales_chart_data
            }
            
            # Add AI predictions if available
            if stock_predictor is not None:
                stock_alerts = stock_predictor.predict_stock_alerts()
                dashboard_data['stock_alerts'] = stock_alerts
                
            if sales_forecaster is not None:
                weekly_trends = sales_forecaster.get_weekly_trends()
                dashboard_data['sales_trends'] = weekly_trends
                
        except Exception as e:
            logger.error(f"Error building dashboard data: {e}")
            # Fallback to minimal dashboard data
            dashboard_data = {
                'total_products': 0,
                'low_stock_items': [],
                'today_sales': 0,
                'total_revenue': 0,
                'pending_debts': 0,
                'cash_balance': 0,
                'recent_activities': [],
                'error': f"Error fetching dashboard data: {str(e)}"
            }
    else:
        # Minimal dashboard data
        dashboard_data = {
            'total_products': 0,
            'low_stock_items': [],
            'today_sales': 0,
            'total_revenue': 0,
            'pending_debts': 0,
            'cash_balance': 0,
            'recent_activities': [],
            'minimal_mode': True
        }

    # Unpack dashboard_data for template variables
    return render_template(
        'dashboard.html',
        **dashboard_data,
        user_role=user_role
    )

@app.route('/inventory')
@login_required
def inventory():
    """Inventory management page"""
    try:
        # Get stats for initial display
        inventory_stats = db_manager.get_inventory_stats() if db_manager is not None else {}
        
        # Prepare context for template
        # Determine currency for server-side formatting if needed
        current_currency = 'MRU'
        try:
            if db_manager is not None:
                settings = db_manager.get_app_settings()
                current_currency = (settings.get('currency') or 'MRU').upper()
        except Exception:
            pass

        context = {
            'total_products': inventory_stats.get('total', 0),
            'in_stock_products': inventory_stats.get('total', 0) - inventory_stats.get('out_of_stock', 0),
            'low_stock_products': inventory_stats.get('low_stock', 0),
            'stock_value': f"{inventory_stats.get('inventory_value', 0):,.0f}",  # numeric only; template will add currency
            'categories': inventory_stats.get('categories', [])
        }

        # Pass debug flag for conditional client assets
        debug_pages = app.config.get('DEBUG_PAGES')
        return render_template('inventory.html', debug_pages=debug_pages, **context)
    except Exception as e:
        print(f"Error loading inventory page: {e}")
        # Fallback with default values
        return render_template(
            'inventory.html',
            total_products=0,
            in_stock_products=0,
            low_stock_products=0,
            stock_value='0',
            categories=[],
            debug_pages=app.config.get('DEBUG_PAGES')
        )


# Debug-only pages are only registered when DEBUG_PAGES is enabled
if app.config.get('DEBUG_PAGES'):
    @app.route('/inventory-launcher')
    def inventory_launcher():
        """Inventory launcher page with auto-login option (debug only)"""
        return render_template('inventory_launcher.html')

    @app.route('/debug/inventory')
    def debug_inventory():
        """Debug page for inventory API (debug only)"""
        return render_template('debug_inventory.html')

    @app.route('/login-test')
    def login_test():
        """Test login and inventory API functionality (debug only)"""
        return render_template('login_test.html')

    @app.route('/test-api')
    def test_api():
        """Test API functionality directly (debug only)"""
        return render_template('test_api.html')

    @app.route('/test-inventory')
    def test_inventory():
        """Test inventory API functionality (debug only)"""
        return render_template('test_inventory.html')

    @app.route('/minimal-test')
    def minimal_test():
        """Minimal test for inventory API (debug only)"""
        return render_template('minimal_test.html')


@app.route('/customers')
@login_required
def customers():
    """Customers management page"""
    return render_template('customers.html')


@app.route('/sales')
@login_required
def sales():
    """Sales management page"""
    return render_template('sales.html')

# Sales API endpoints
@app.route('/api/sales/stats')
@login_required
def sales_stats():
    """Get sales statistics"""
    if MODULES_AVAILABLE and db_manager is not None:
        try:
            # Determine currency
            current_currency = 'MRU'
            try:
                settings = db_manager.get_app_settings()
                current_currency = (settings.get('currency') or 'MRU').upper()
            except Exception:
                pass
            # Get sales statistics from database
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Today's sales
            today_sales_data = db_manager.get_today_sales() if db_manager is not None else {'total': 0, 'count': 0}
            
            # Get today's date
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get yesterday's sales
            cursor.execute('''
                SELECT SUM(total_amount) as total, COUNT(*) as count
                FROM sales
                WHERE DATE(sale_date) = DATE(?, '-1 day')
                AND is_deleted = 0
            ''', (today,))
            
            yesterday_data = cursor.fetchone()
            yesterday_sales = {
                'total': float(yesterday_data['total']) if yesterday_data and yesterday_data['total'] else 0,
                'count': yesterday_data['count'] if yesterday_data else 0
            }
            
            # Get sales for this week
            cursor.execute('''
                SELECT SUM(total_amount) as total, COUNT(*) as count
                FROM sales
                WHERE sale_date >= DATE(?, 'weekday 0', '-7 days')
                AND is_deleted = 0
            ''', (today,))
            
            weekly_data = cursor.fetchone()
            weekly_sales = {
                'total': float(weekly_data['total']) if weekly_data and weekly_data['total'] else 0,
                'count': weekly_data['count'] if weekly_data else 0
            }
            
            # Get sales for this month
            cursor.execute('''
                SELECT SUM(total_amount) as total, COUNT(*) as count
                FROM sales
                WHERE strftime('%Y-%m', sale_date) = strftime('%Y-%m', ?)
                AND is_deleted = 0
            ''', (today,))
            
            monthly_data = cursor.fetchone()
            monthly_sales = {
                'total': float(monthly_data['total']) if monthly_data and monthly_data['total'] else 0,
                'count': monthly_data['count'] if monthly_data else 0
            }
            
            # Get total pending credits (support DBs without remaining_amount and legacy paid column)
            cursor.execute('PRAGMA table_info(sales)')
            sales_cols = [col[1] for col in cursor.fetchall()]
            if 'remaining_amount' in sales_cols:
                cursor.execute('''
                    SELECT SUM(remaining_amount) as total, COUNT(*) as count
                    FROM sales
                    WHERE remaining_amount > 0
                    AND is_deleted = 0
                ''')
            else:
                paid_col = 'amount_paid' if 'amount_paid' in sales_cols else ('paid_amount' if 'paid_amount' in sales_cols else None)
                if paid_col:
                    cursor.execute(
                        f'''
                        SELECT SUM(total_amount - {paid_col}) as total,
                               SUM(CASE WHEN total_amount > {paid_col} THEN 1 ELSE 0 END) as count
                        FROM sales
                        WHERE (total_amount - {paid_col}) > 0
                        AND is_deleted = 0
                        '''
                    )
                else:
                    # No paid column, nothing to compute
                    credit_data = {'total': 0, 'count': 0}
                    credits = {
                        'total': 0,
                        'count': 0
                    }
                    # Continue to formatting block
                    
            credit_data = cursor.fetchone()
            credits = {
                'total': float(credit_data['total']) if credit_data and credit_data['total'] else 0,
                'count': credit_data['count'] if credit_data else 0
            }
            
        # Format values
            stats = {
                'today': {
            'total': f"{today_sales_data.get('total', 0):,.2f} {current_currency}",
                    'count': today_sales_data.get('count', 0)
                },
                'yesterday': {
            'total': f"{yesterday_sales['total']:,.2f} {current_currency}",
                    'count': yesterday_sales['count']
                },
                'weekly': {
            'total': f"{weekly_sales['total']:,.2f} {current_currency}",
                    'count': weekly_sales['count']
                },
                'monthly': {
            'total': f"{monthly_sales['total']:,.2f} {current_currency}",
                    'count': monthly_sales['count']
                },
                'credits': {
            'total': f"{credits['total']:,.2f} {current_currency}",
                    'count': credits['count']
                }
            }
            
            return jsonify({'success': True, 'stats': stats})
        except Exception as e:
            logger.error(f"Error fetching sales stats: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        # Fallback data for minimal mode
        current_currency = 'MRU'
        try:
            if db_manager is not None:
                settings = db_manager.get_app_settings()
                current_currency = (settings.get('currency') or 'MRU').upper()
        except Exception:
            pass
        return jsonify({
            'success': False,
            'message': 'Sales statistics not available in minimal mode',
            'stats': {
                'today': {'total': f'0.00 {current_currency}', 'count': 0},
                'yesterday': {'total': f'0.00 {current_currency}', 'count': 0},
                'weekly': {'total': f'0.00 {current_currency}', 'count': 0},
                'monthly': {'total': f'0.00 {current_currency}', 'count': 0},
                'credits': {'total': f'0.00 {current_currency}', 'count': 0}
            }
        })

@app.route('/api/sales/list')
@login_required
def sales_list():
    """Get sales list with pagination and filtering"""
    if MODULES_AVAILABLE and db_manager is not None:
        try:
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            search = request.args.get('search', '')
            payment_status = request.args.get('payment_status', '')
            date_from = request.args.get('date_from', '')
            date_to = request.args.get('date_to', '')
            
            # Calculate offset
            offset = (page - 1) * limit
            
            # Build query
            query = '''
                SELECT s.*, u.username as seller_name, c.name as customer_name
                FROM sales s
                LEFT JOIN users u ON s.created_by = u.id
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.is_deleted = 0
            '''
            params = []
            
            # Add search filter
            if search:
                query += ''' AND (
                    s.invoice_number LIKE ? 
                    OR c.name LIKE ?
                    OR u.username LIKE ?
                )'''
                search_param = f'%{search}%'
                params.extend([search_param, search_param, search_param])
            
            # Add payment status filter
            if payment_status in ['paid', 'partial', 'unpaid']:
                query += ' AND s.payment_status = ?'
                params.append(payment_status)
            
            # Add date range filter
            if date_from:
                query += ' AND s.sale_date >= ?'
                params.append(date_from)
            
            if date_to:
                query += ' AND s.sale_date <= ?'
                params.append(date_to)
            
            # Add sorting
            query += ' ORDER BY s.sale_date DESC'
            
            # Add pagination
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            # Execute query
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # Convert rows to dictionaries
            sales = []
            for row in cursor.fetchall():
                sale = dict(row)
                
                # Format date
                if 'sale_date' in sale:
                    try:
                        sale_date = datetime.fromisoformat(sale['sale_date'].replace('Z', '+00:00'))
                        sale['formatted_date'] = sale_date.strftime('%d/%m/%Y %H:%M')
                    except Exception:
                        sale['formatted_date'] = sale['sale_date']
                
                sales.append(sale)
            
            # Get total count for pagination
            count_query = '''
                SELECT COUNT(*) as total
                FROM sales s
                LEFT JOIN users u ON s.created_by = u.id
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.is_deleted = 0
            '''
            count_params = []
            
            # Add the same filters to count query
            if search:
                count_query += ''' AND (
                    s.invoice_number LIKE ? 
                    OR c.name LIKE ?
                    OR u.username LIKE ?
                )'''
                search_param = f'%{search}%'
                count_params.extend([search_param, search_param, search_param])
            
            if payment_status in ['paid', 'partial', 'unpaid']:
                count_query += ' AND s.payment_status = ?'
                count_params.append(payment_status)
            
            if date_from:
                count_query += ' AND s.sale_date >= ?'
                count_params.append(date_from)
            
            if date_to:
                count_query += ' AND s.sale_date <= ?'
                count_params.append(date_to)
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']
            
            # Calculate pagination info
            pagination = {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
            
            return jsonify({
                'success': True, 
                'sales': sales,
                'pagination': pagination
            })
        except Exception as e:
            logger.error(f"Error fetching sales: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        # Fallback empty list for minimal mode
        return jsonify({
            'success': False,
            'message': 'Sales data not available in minimal mode',
            'sales': [],
            'pagination': {
                'page': 1,
                'limit': 20,
                'total': 0,
                'pages': 0
            }
        })

@app.route('/finance')
@login_required
def finance():
    """Financial management page"""
    return render_template('finance.html')

# Finance API endpoints
@app.route('/api/finance/summary')
@login_required
def finance_summary():
    """Get financial summary data"""
    if MODULES_AVAILABLE and db_manager is not None:
        try:
            # Get financial data from database
            total_revenue = db_manager.get_total_revenue() if db_manager is not None else 0
            
            # Get expenses 
            conn = db_manager.get_connection() if db_manager is not None else None
            total_expenses = 0
            
            if conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT SUM(amount) as total_expenses
                    FROM expenses
                    WHERE is_deleted = 0
                ''')
                result = cursor.fetchone()
                if result and result['total_expenses']:
                    total_expenses = float(result['total_expenses'])
            
            # Calculate net profit
            net_profit = total_revenue - total_expenses
            
            # Get cash balance
            cash_balance = db_manager.get_cash_balance() if db_manager is not None else 0
            
            current_currency = 'MRU'
            try:
                settings = db_manager.get_app_settings()
                current_currency = (settings.get('currency') or 'MRU').upper()
            except Exception:
                pass
            # Format values
            summary = {
                'total_revenue': f"{total_revenue:,.2f} {current_currency}",
                'total_expenses': f"{total_expenses:,.2f} {current_currency}",
                'net_profit': f"{net_profit:,.2f} {current_currency}",
                'cash_balance': f"{cash_balance:,.2f} {current_currency}"
            }
            
            return jsonify({'success': True, 'summary': summary})
        except Exception as e:
            logger.error(f"Error fetching finance summary: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        # Fallback data for minimal mode
        current_currency = 'MRU'
        try:
            if db_manager is not None:
                settings = db_manager.get_app_settings()
                current_currency = (settings.get('currency') or 'MRU').upper()
        except Exception:
            pass
        return jsonify({
            'success': False,
            'message': 'Financial data not available in minimal mode',
            'summary': {
                'total_revenue': f'0.00 {current_currency}',
                'total_expenses': f'0.00 {current_currency}',
                'net_profit': f'0.00 {current_currency}',
                'cash_balance': f'0.00 {current_currency}'
            }
        })

@app.route('/api/finance/transactions')
@login_required
def finance_transactions():
    """Get financial transactions"""
    if MODULES_AVAILABLE and db_manager is not None:
        try:
            # Get transactions from database
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Combine income and expenses for a complete transaction list
            cursor.execute('''
                SELECT 
                    'income' as type,
                    s.id,
                    s.sale_date as date,
                    'Vente #' || s.id as description,
                    s.total_amount as amount,
                    'Ventes' as category
                FROM sales s
                WHERE s.is_deleted = 0
                UNION
                SELECT 
                    'expense' as type,
                    e.id,
                    e.expense_date as date,
                    e.description,
                    e.amount,
                    e.category
                FROM expenses e
                WHERE e.is_deleted = 0
                ORDER BY date DESC
                LIMIT 100
            ''')
            
            # Convert rows to dictionaries
            transactions = []
            for row in cursor.fetchall():
                transaction = dict(row)
                transactions.append(transaction)
            
            return jsonify({'success': True, 'transactions': transactions})
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        # Fallback empty list for minimal mode
        return jsonify({
            'success': False,
            'message': 'Transaction data not available in minimal mode',
            'transactions': []
        })

@app.route('/api/finance/charts')
@login_required
def finance_charts():
    """Get financial chart data"""
    if MODULES_AVAILABLE and db_manager is not None:
        try:
            # Get period from request
            period = request.args.get('period', 'month')
            
            # Determine date range based on period
            today = datetime.now()
            if period == 'week':
                start_date = today - timedelta(days=7)
                date_format = '%d %b'  # Day Month format
                labels = [(today - timedelta(days=i)).strftime(date_format) for i in range(7, -1, -1)]
            elif period == 'month':
                start_date = today - timedelta(days=30)
                date_format = '%d %b'
                labels = [(today - timedelta(days=i)).strftime(date_format) for i in range(30, -1, -5)]
            else:  # year
                start_date = today - timedelta(days=365)
                date_format = '%b %Y'  # Month Year format
                labels = []
                for i in range(12):
                    month_date = today - timedelta(days=30 * (11 - i))
                    labels.append(month_date.strftime(date_format))
            
            # Get revenue data
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # For revenue data
            cursor.execute('''
                SELECT 
                    strftime(?, sale_date) as period,
                    SUM(total_amount) as amount
                FROM sales
                WHERE sale_date >= ?
                AND is_deleted = 0
                GROUP BY period
                ORDER BY sale_date
            ''', (date_format, start_date.strftime('%Y-%m-%d')))
            
            revenue_data = {row['period']: float(row['amount']) for row in cursor.fetchall()}
            
            # For expense data
            cursor.execute('''
                SELECT 
                    strftime(?, expense_date) as period,
                    SUM(amount) as amount
                FROM expenses
                WHERE expense_date >= ?
                AND is_deleted = 0
                GROUP BY period
                ORDER BY expense_date
            ''', (date_format, start_date.strftime('%Y-%m-%d')))
            
            expense_data = {row['period']: float(row['amount']) for row in cursor.fetchall()}
            
            # For expense categories
            cursor.execute('''
                SELECT 
                    category,
                    SUM(amount) as amount
                FROM expenses
                WHERE expense_date >= ?
                AND is_deleted = 0
                GROUP BY category
                ORDER BY amount DESC
            ''', (start_date.strftime('%Y-%m-%d'),))
            
            expense_categories = []
            expense_amounts = []
            
            for row in cursor.fetchall():
                expense_categories.append(row['category'])
                expense_amounts.append(float(row['amount']))
            
            # Prepare revenue and expense datasets
            revenue_values = []
            expense_values = []
            
            for label in labels:
                revenue_values.append(revenue_data.get(label, 0))
                expense_values.append(expense_data.get(label, 0))
            
            # Return chart data
            chart_data = {
                'revenue': {
                    'labels': labels,
                    'data': revenue_values
                },
                'expense': {
                    'categories': expense_categories,
                    'data': expense_amounts
                }
            }
            
            return jsonify({'success': True, 'chart_data': chart_data})
        except Exception as e:
            logger.error(f"Error fetching chart data: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        # Fallback empty chart data for minimal mode
        return jsonify({
            'success': False,
            'message': 'Chart data not available in minimal mode'
        })

@app.route('/reports')
@login_required
def reports():
    """Reports and analytics page"""
    return render_template('reports.html')

# Reports API endpoints
@app.route('/api/reports/sales')
@login_required
def reports_sales():
    """Get sales reports data"""
    if MODULES_AVAILABLE and db_manager is not None:
        try:
            # Get period parameter
            period = request.args.get('period', 'monthly')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            
            # Current date
            today = datetime.now()
            
            # Set default date range if not provided
            if not start_date:
                if period == 'daily':
                    start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
                elif period == 'weekly':
                    start_date = (today - timedelta(days=8 * 7)).strftime('%Y-%m-%d')  # 8 weeks
                elif period == 'monthly':
                    start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')  # 1 year
                else:
                    start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
            
            if not end_date:
                end_date = today.strftime('%Y-%m-%d')
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get time format and group based on period
            if period == 'daily':
                time_format = '%Y-%m-%d'
                group_by = "strftime('%Y-%m-%d', sale_date)"
                label_format = '%d %b'
            elif period == 'weekly':
                time_format = '%Y-W%W'
                group_by = "strftime('%Y-W%W', sale_date)"
                label_format = 'Week %W'
            elif period == 'monthly':
                time_format = '%Y-%m'
                group_by = "strftime('%Y-%m', sale_date)"
                label_format = '%b %Y'
            else:  # yearly
                time_format = '%Y'
                group_by = "strftime('%Y', sale_date)"
                label_format = '%Y'
            
            # Get sales data by period
            cursor.execute(f'''
                SELECT 
                    {group_by} as period,
                    SUM(total_amount) as total,
                    COUNT(*) as count,
                    AVG(total_amount) as average
                FROM sales
                WHERE sale_date BETWEEN ? AND ?
                AND is_deleted = 0
                GROUP BY period
                ORDER BY period
            ''', (start_date, end_date))
            
            # Process results
            periods = []
            totals = []
            counts = []
            averages = []
            
            for row in cursor.fetchall():
                # Convert period format for display
                if period == 'weekly':
                    year, week = row['period'].split('-W')
                    # Create a date object for the first day of the week
                    date_obj = datetime.strptime(f'{year}-{week}-1', '%Y-%W-%w')
                    periods.append(f"{date_obj.strftime('%d %b')} - {(date_obj + timedelta(days=6)).strftime('%d %b')}")
                else:
                    date_obj = datetime.strptime(row['period'], time_format)
                    periods.append(date_obj.strftime(label_format))
                
                totals.append(float(row['total']) if row['total'] else 0)
                counts.append(row['count'])
                averages.append(float(row['average']) if row['average'] else 0)
            
            # Get product sales breakdown
            # Prefer new schema (sale_items); gracefully fallback to legacy (sale_details)
            top_products = []
            try:
                cursor.execute('''
                    SELECT 
                        p.name as product_name,
                        SUM(si.quantity) as quantity,
                        SUM(si.quantity * si.unit_price) as total
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    JOIN sales s ON si.sale_id = s.id
                    WHERE s.sale_date BETWEEN ? AND ?
                    AND s.is_deleted = 0
                    GROUP BY si.product_id
                    ORDER BY total DESC
                    LIMIT 10
                ''', (start_date, end_date))
            except Exception:
                cursor.execute('''
                    SELECT 
                        p.name as product_name,
                        SUM(sd.quantity) as quantity,
                        SUM(sd.quantity * sd.unit_price) as total
                    FROM sale_details sd
                    JOIN products p ON sd.product_id = p.id
                    JOIN sales s ON sd.sale_id = s.id
                    WHERE s.sale_date BETWEEN ? AND ?
                    AND s.is_deleted = 0
                    GROUP BY sd.product_id
                    ORDER BY total DESC
                    LIMIT 10
                ''', (start_date, end_date))
            
            for row in cursor.fetchall():
                top_products.append({
                    'name': row['product_name'],
                    'quantity': row['quantity'],
                    'total': float(row['total']) if row['total'] else 0
                })
            
            # Get payment method breakdown
            cursor.execute('''
                SELECT 
                    payment_method,
                    COUNT(*) as count,
                    SUM(amount_paid) as total
                FROM sales
                WHERE sale_date BETWEEN ? AND ?
                AND is_deleted = 0
                GROUP BY payment_method
                ORDER BY total DESC
            ''', (start_date, end_date))
            
            payment_methods = []
            for row in cursor.fetchall():
                payment_methods.append({
                    'method': row['payment_method'],
                    'count': row['count'],
                    'total': float(row['total']) if row['total'] else 0
                })
            
            # Calculate summary
            total_sales = sum(totals)
            avg_sales = sum(totals) / len(totals) if totals else 0
            total_transactions = sum(counts)
            
            current_currency = 'MRU'
            try:
                settings = db_manager.get_app_settings()
                current_currency = (settings.get('currency') or 'MRU').upper()
            except Exception:
                pass
            summary = {
                'total_sales': f"{total_sales:,.2f} {current_currency}",
                'total_transactions': total_transactions,
                'average_per_period': f"{avg_sales:,.2f} {current_currency}",
                'average_per_transaction': f"{(total_sales / total_transactions if total_transactions else 0):,.2f} {current_currency}"
            }
            
            # Return all report data
            report_data = {
                'summary': summary,
                'chart_data': {
                    'periods': periods,
                    'totals': totals,
                    'counts': counts,
                    'averages': averages
                },
                'top_products': top_products,
                'payment_methods': payment_methods
            }
            
            return jsonify({'success': True, 'report': report_data})
        except Exception as e:
            logger.error(f"Error generating sales report: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        # Fallback data for minimal mode
        return jsonify({
            'success': False,
            'message': 'Reports not available in minimal mode'
        })

@app.route('/api/reports/inventory')
@login_required
def reports_inventory():
    """Get inventory reports data"""
    if MODULES_AVAILABLE and db_manager is not None:
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get inventory value by category
            cursor.execute('''
                SELECT 
                    category,
                    COUNT(*) as product_count,
                    SUM(current_stock) as total_items,
                    SUM(current_stock * purchase_price) as total_value
                FROM products
                WHERE is_active = 1
                GROUP BY category
                ORDER BY total_value DESC
            ''')
            
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    'name': row['category'],
                    'count': row['product_count'],
                    'items': row['total_items'],
                    'value': float(row['total_value']) if row['total_value'] else 0
                })
            
            # Get top valuable products
            cursor.execute('''
                SELECT 
                    name,
                    sku,
                    current_stock,
                    purchase_price,
                    (current_stock * purchase_price) as stock_value
                FROM products
                WHERE is_active = 1
                ORDER BY stock_value DESC
                LIMIT 10
            ''')
            
            valuable_products = []
            for row in cursor.fetchall():
                valuable_products.append({
                    'name': row['name'],
                    'sku': row['sku'],
                    'stock': row['current_stock'],
                    'price': float(row['purchase_price']) if row['purchase_price'] else 0,
                    'value': float(row['stock_value']) if row['stock_value'] else 0
                })
            
            # Get low stock items
            low_stock_items = db_manager.get_low_stock_items(limit=10) if db_manager is not None else []
            
            # Get inventory movement trends (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m-%d', movement_date) as date,
                    movement_type,
                    COUNT(*) as count,
                    SUM(quantity) as total_quantity
                FROM inventory_movements
                WHERE movement_date >= ?
                GROUP BY date, movement_type
                ORDER BY date
            ''', (thirty_days_ago,))
            
            movement_trends = {}
            for row in cursor.fetchall():
                date = row['date']
                if date not in movement_trends:
                    movement_trends[date] = {'in': 0, 'out': 0}
                
                if row['movement_type'] == 'in':
                    movement_trends[date]['in'] = row['total_quantity']
                elif row['movement_type'] == 'out':
                    movement_trends[date]['out'] = row['total_quantity']
            
            # Convert to arrays for charting
            dates = sorted(movement_trends.keys())
            stock_in = [movement_trends[date]['in'] for date in dates]
            stock_out = [movement_trends[date]['out'] for date in dates]
            
            # Calculate overall value
            cursor.execute('''
                SELECT 
                    SUM(current_stock * purchase_price) as total_value,
                    COUNT(*) as total_products,
                    SUM(current_stock) as total_items
                FROM products
                WHERE is_active = 1
            ''')
            
            result = cursor.fetchone()
            total_value = float(result['total_value']) if result and result['total_value'] else 0
            total_products = result['total_products'] if result else 0
            total_items = result['total_items'] if result else 0
            
            # Prepare summary
            current_currency = 'MRU'
            try:
                settings = db_manager.get_app_settings()
                current_currency = (settings.get('currency') or 'MRU').upper()
            except Exception:
                pass
            summary = {
                'total_value': f"{total_value:,.2f} {current_currency}",
                'total_products': total_products,
                'total_items': total_items,
                'low_stock_count': len(low_stock_items) if isinstance(low_stock_items, list) else 0
            }
            
            # Return report data
            report_data = {
                'summary': summary,
                'categories': categories,
                'valuable_products': valuable_products,
                'low_stock_items': low_stock_items,
                'movement_trends': {
                    'dates': dates,
                    'stock_in': stock_in,
                    'stock_out': stock_out
                }
            }
            
            return jsonify({'success': True, 'report': report_data})
        except Exception as e:
            logger.error(f"Error generating inventory report: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        # Fallback data for minimal mode
        return jsonify({
            'success': False,
            'message': 'Reports not available in minimal mode'
        })

@app.route('/admin')
@admin_required
def admin():
    """Admin panel"""
    return render_template('admin.html')

@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    current_user = session.get('username', 'Guest')
    user_role = session.get('user_role', 'guest')
    current_language = session.get('language', 'fr')
    app_version = "1.0.0"  # This could be stored in a config file
    
    return render_template(
        'settings.html',
        current_user=current_user,
        user_role=user_role,
        current_language=current_language,
        app_version=app_version,
        current_year=datetime.now().year
    )

# Note: Settings API endpoints have been moved to api/settings.py module

@app.route('/set-language/<language>', methods=['GET', 'POST'])
def set_language(language):
    """Set user's preferred language"""
    if language in SUPPORTED_LANGUAGES:
        session['language'] = language
        # Update user preferences in database if user is logged in
        if 'user_id' in session and db_manager is not None:
            db_manager.update_user_language(session['user_id'], language)
            flash(f'Langue changée vers {SUPPORTED_LANGUAGES[language]}', 'success')
    
    # Get redirect URL from query param or use default
    redirect_url = request.args.get('redirect', url_for('dashboard'))
    
    # If not logged in, redirect to login page
    if 'user_id' not in session:
        redirect_url = url_for('login')
    
    return redirect(redirect_url)

# Dashboard API endpoints are provided by the dashboard blueprint (/api/dashboard/*)

# Dashboard activities are served by the dashboard blueprint

# API Routes for offline synchronization
@app.route('/api/sync/status')
@login_required
def sync_status():
    """Get synchronization status"""
    if MODULES_AVAILABLE and sync_manager is not None:
        status = sync_manager.get_sync_status()
        return jsonify({'success': True, **status})
    else:
        return jsonify({'success': False, 'message': 'Sync not available in minimal mode'})

@app.route('/api/sync/push', methods=['POST'])
@login_required
def sync_push():
    """Push local changes to cloud"""
    if not MODULES_AVAILABLE or sync_manager is None:
        return jsonify({'success': False, 'error': 'Sync not available in minimal mode'})
    
    try:
        data = request.json or {}
        force_sync = data.get('force', False)
        result = sync_manager.push_changes(force_sync)
        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"Error in sync_push: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sync/pull', methods=['POST'])
@login_required
def sync_pull():
    """Pull changes from cloud"""
    if not MODULES_AVAILABLE or sync_manager is None:
        return jsonify({'success': False, 'error': 'Sync not available in minimal mode'})
    
    try:
        result = sync_manager.pull_changes()
        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"Error in sync_pull: {e}")
        return jsonify({'success': False, 'error': str(e)})

# AI Forecasting and Analytics
@app.route('/api/forecast/demand')
@login_required
def forecast_demand():
    """Get demand forecasting"""
    if not MODULES_AVAILABLE or 'sales_forecaster' not in globals():
        return jsonify({
            'success': False,
            'message': 'Forecasting not available in minimal mode'
        })
    
    try:
        product_id = request.args.get('product_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        # Make sure we have a valid product_id
        if product_id is None:
            return jsonify({'success': False, 'error': 'Product ID is required'})
        
        # Use the actual forecasting model for the specified product
        if sales_forecaster is not None:
            forecast = sales_forecaster.predict_product_sales(product_id, days)
            return jsonify({
                'success': True, 
                'forecast': forecast
            })
        else:
            return jsonify({'success': False, 'error': 'Sales forecaster not available'})
    except Exception as e:
        logger.error(f"Error in forecast_demand: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/forecast/reorder')
@login_required
def forecast_reorder():
    """Get reorder recommendations"""
    if not MODULES_AVAILABLE or 'stock_predictor' not in globals():
        return jsonify({
            'success': False,
            'message': 'AI recommendations not available in minimal mode'
        })
    
    try:
        # Use the actual stock recommendation method
        if stock_predictor is not None:
            recommendations = stock_predictor.generate_restock_suggestions()
            return jsonify({
                'success': True, 
                'recommendations': recommendations
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Stock predictor not available'
            })
    except Exception as e:
        logger.error(f"Error in forecast_reorder: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics/trends')
@login_required
def analytics_trends():
    """Get sales trends analysis"""
    if not MODULES_AVAILABLE or 'sales_forecaster' not in globals():
        return jsonify({
            'success': False,
            'message': 'Analytics not available in minimal mode'
        })
    
    try:
        period = request.args.get('period', 'monthly')
        
        if sales_forecaster is None:
            return jsonify({
                'success': False,
                'message': 'Sales forecaster not available'
            })
        
        # Get actual weekly trends data
        weekly_trends = sales_forecaster.get_weekly_trends()
        
        # Get overall sales prediction for the next 30 days
        sales_prediction = sales_forecaster.predict_overall_sales(days_ahead=30)
        
        # Combine the data
        trends = {
            'weekly_trends': weekly_trends,
            'sales_prediction': sales_prediction
        }
        
        return jsonify({'success': True, 'trends': trends})
    except Exception as e:
        logger.error(f"Error in analytics_trends: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error_code=404, error_message='Page non trouvée'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message='Erreur interne du serveur'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html', error_code=403, error_message='Accès interdit'), 403

# (Routes for sw.js and manifest.json are already defined above as serve_service_worker_file and serve_manifest_file)

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)
