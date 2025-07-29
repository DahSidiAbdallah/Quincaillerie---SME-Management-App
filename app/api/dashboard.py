#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard API for Quincaillerie & SME Management App
Provides endpoints for dashboard data
"""

from flask import Blueprint, jsonify, session
from datetime import datetime, timedelta
import logging
from db.database import DatabaseManager

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)
db_manager = DatabaseManager()

@dashboard_bp.route('/stats')
def get_dashboard_stats():
    """Get all dashboard statistics in a single API call"""
    try:
        # Get basic stats
        total_products = db_manager.get_total_products()
        
        # Get low stock items
        low_stock_items = db_manager.get_low_stock_items()
        
        # Get today's sales
        today_sales = db_manager.get_today_sales()
        today_sales_count = today_sales.get('count', 0)
        today_sales_amount = today_sales.get('total', 0)
        
        # Get pending debts
        pending_debts = db_manager.get_pending_debts()
        pending_debts_count = pending_debts.get('count', 0)
        pending_debts_amount = pending_debts.get('total', 0)
        
        # Get total revenue
        total_revenue = db_manager.get_total_revenue()
        
        # Get cash balance
        cash_balance = db_manager.get_cash_balance()
        
        # Format monetary values with commas
        def format_money(value):
            if isinstance(value, (int, float)):
                return f"{value:,.2f}".replace(',', ' ').replace('.', ',')
            return "0,00"
        
        # Calculate yesterday's sales for comparison
        # This would require a new method in DatabaseManager
        yesterday = (datetime.now() - timedelta(days=1)).date()
        yesterday_sales = 0  # This would need implementation in DatabaseManager
        
        # Calculate sales change percentage
        sales_change = 0
        if yesterday_sales > 0:
            sales_change = ((today_sales_amount - yesterday_sales) / yesterday_sales) * 100
        
        # Return formatted stats
        return jsonify({
            'success': True,
            'stats': {
                'total_products': total_products,
                'low_stock_count': len(low_stock_items),
                'low_stock_items': low_stock_items,
                'today_sales_count': today_sales_count,
                'today_sales': format_money(today_sales_amount),
                'total_revenue': format_money(total_revenue),
                'pending_debts_count': pending_debts_count,
                'pending_debts': format_money(pending_debts_amount),
                'cash_balance': format_money(cash_balance),
                'sales_change': round(sales_change, 1)
            }
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/activities')
def get_dashboard_activities():
    """Get recent activities for dashboard"""
    try:
        activities = db_manager.get_recent_activities(limit=10)
        
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
        
        # Format monetary values
        for product in products:
            if 'total_amount' in product and product['total_amount']:
                product['total_amount'] = f"{product['total_amount']:,.2f}".replace(',', ' ').replace('.', ',')
        
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
