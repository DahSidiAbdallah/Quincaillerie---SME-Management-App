#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard API for Quincaillerie & SME Management App
Provides endpoints for dashboard data
"""

from flask import Blueprint, jsonify, session, request
from datetime import datetime, timedelta
import logging
from db.database import DatabaseManager

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)
db_manager = DatabaseManager()

@dashboard_bp.route('/stats')
def get_dashboard_stats():
    """Get all dashboard statistics in a single API call (numeric values)."""
    try:
        # Get basic stats
        total_products = db_manager.get_total_products()

        # Get low stock items
        low_stock_items = db_manager.get_low_stock_items()

        # Get today's sales
        today_sales = db_manager.get_today_sales()
        today_sales_count = today_sales.get('count', 0)
        today_sales_amount = today_sales.get('total', 0) or 0

        # Get pending debts
        pending_debts = db_manager.get_pending_debts()
        pending_debts_count = pending_debts.get('count', 0)
        pending_debts_amount = pending_debts.get('total', 0) or 0

        # Get total revenue
        total_revenue = db_manager.get_total_revenue() or 0

        # Get cash balance
        cash_balance = db_manager.get_cash_balance() or 0

        # Calculate yesterday's sales for comparison
        yesterday_total = 0.0
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                '''
                SELECT SUM(total_amount) as total, COUNT(*) as count
                FROM sales
                WHERE DATE(sale_date) = DATE(?, '-1 day')
                AND is_deleted = 0
                ''',
                (today,),
            )
            row = cursor.fetchone()
            if row and row['total'] is not None:
                yesterday_total = float(row['total']) or 0.0
        except Exception as _e:
            yesterday_total = 0.0
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

        # Calculate sales change percentage
        sales_change = 0.0
        if yesterday_total and yesterday_total > 0:
            try:
                sales_change = ((float(today_sales_amount) - float(yesterday_total)) / float(yesterday_total)) * 100.0
            except Exception:
                sales_change = 0.0

        # Return numeric stats (frontend formats currency)
        return jsonify({
            'success': True,
            'stats': {
                'total_products': int(total_products or 0),
                'low_stock_count': len(low_stock_items) if isinstance(low_stock_items, list) else int(low_stock_items or 0),
                'low_stock_items': low_stock_items,
                'today_sales_count': int(today_sales_count or 0),
                'today_sales': float(today_sales_amount or 0),
                'total_revenue': float(total_revenue or 0),
                'pending_debts_count': int(pending_debts_count or 0),
                'pending_debts': float(pending_debts_amount or 0),
                'cash_balance': float(cash_balance or 0),
                'sales_change': round(float(sales_change), 1)
            }
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/yesterday-sales')
def get_yesterday_sales():
    """Get yesterday's sales summary (total and count)."""
    conn = None
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            '''
            SELECT SUM(total_amount) as total, COUNT(*) as count
            FROM sales
            WHERE DATE(sale_date) = DATE(?, '-1 day')
            AND is_deleted = 0
            ''',
            (today,),
        )
        row = cursor.fetchone()
        result = {
            'total': float(row['total']) if row and row['total'] else 0.0,
            'count': int(row['count']) if row and row['count'] else 0,
        }
        return jsonify({'success': True, 'yesterday': result})
    except Exception as e:
        logger.error(f"Error fetching yesterday sales: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass

@dashboard_bp.route('/activities')
def get_dashboard_activities():
    """Get recent activities for dashboard"""
    try:
        limit = int(request.args.get('limit', 10))
        activities = db_manager.get_recent_activities(limit=limit)
        
        # Format activities for frontend display
        formatted_activities = []
        for activity in activities:
            activity_type = determine_activity_type(activity.get('action_type', ''))
            time_ago = format_time_ago(activity.get('created_at', ''))
            
            formatted_activities.append({
                'type': activity_type,
                'title': activity.get('action_type', 'Action'),
                'description': activity.get('description', ''),
                'time_ago': time_ago,
                'user': activity.get('username', '')
            })
        
        return jsonify({'success': True, 'activities': formatted_activities})
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/top-products')
def get_top_products():
    """Get top selling products"""
    try:
        # Get top selling products
        products = db_manager.get_top_selling_products(days=30, limit=5)
        # Fallback: if no recent sales, broaden the window to all-time to avoid empty UI
        if not products:
            products = db_manager.get_top_selling_products(days=3650, limit=5)
        # Ensure numeric monetary values are returned (frontend applies formatting)
        for product in products:
            try:
                if 'total_sales' in product and product['total_sales'] is not None:
                    product['total_sales'] = float(product['total_sales'])
                if 'quantity_sold' in product and product['quantity_sold'] is not None:
                    product['quantity_sold'] = int(product['quantity_sold'])
            except Exception:
                # If casting fails, leave as-is
                pass
        
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        logger.error(f"Error fetching top products: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/sales-chart')
def get_sales_chart_data():
    """Get data for sales chart"""
    try:
        # Get sales chart data
        chart_data = db_manager.get_sales_chart_data(days=7)
        
        return jsonify({
            'success': True, 
            'daily': chart_data['daily'],
            'weekly': chart_data['weekly']
        })
    except Exception as e:
        logger.error(f"Error fetching sales chart data: {e}")
        return jsonify({'success': False, 'error': str(e)})

def determine_activity_type(action_type):
    """Determine activity type based on action_type"""
    action_type = action_type.lower()
    
    if 'vente' in action_type or 'sale' in action_type:
        return 'sale'
    elif 'stock' in action_type or 'inventory' in action_type:
        return 'stock'
    elif 'login' in action_type or 'connexion' in action_type:
        return 'login'
    elif 'paiement' in action_type or 'payment' in action_type:
        return 'payment'
    else:
        return 'other'

def format_time_ago(timestamp_str):
    """Format timestamp as 'time ago'"""
    if not timestamp_str:
        return "Récemment"
    
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "À l'instant"
    except Exception:
        return "Récemment"
