#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reports API Blueprint
Handles report generation, data export, and analytics
"""

from flask import Blueprint, request, jsonify, session, send_file
from db.database import DatabaseManager
import logging
import json
import io
import csv
from datetime import datetime, date, timedelta
import tempfile
import os

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)
db_manager = DatabaseManager()

def require_auth():
    """Check if user is authenticated"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    return None

@reports_bp.route('/sales-report', methods=['GET'])
def generate_sales_report():
    """Generate comprehensive sales report"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get parameters with clear defaults
        today = date.today().isoformat()
        # Default to all-time data for reports if no date range specified
        start_date = request.args.get('start_date', '2000-01-01')
        end_date = request.args.get('end_date', today)
        group_by = request.args.get('group_by', 'day')  # day, week, month
        
        # Add report metadata for clarity
        report_metadata = {
            'report_type': 'Sales Report',
            'date_range': f'From {start_date} to {end_date}',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'report_notes': 'This report shows historical data across all time by default.'
        }
        
        # Sales summary by period
        if group_by == 'day':
            date_format = '%Y-%m-%d'
            group_clause = 'DATE(s.sale_date)'
        elif group_by == 'week':
            date_format = '%Y-W%W'
            group_clause = 'strftime("%Y-W%W", s.sale_date)'
        else:  # month
            date_format = '%Y-%m'
            group_clause = 'strftime("%Y-%m", s.sale_date)'
        
        cursor.execute(f'''
            SELECT {group_clause} as period,
                   COUNT(*) as sales_count,
                   SUM(s.total_amount) as total_revenue,
                   SUM(CASE WHEN s.is_credit = 1 THEN s.total_amount ELSE 0 END) as credit_sales,
                   SUM((SELECT SUM(si.profit_margin) FROM sale_items si WHERE si.sale_id = s.id)) as total_profit
            FROM sales s
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY {group_clause}
            ORDER BY period DESC
        ''', (start_date, end_date))
        
        sales_by_period = [dict(row) for row in cursor.fetchall()]
        
        # Top selling products
        cursor.execute('''
            SELECT p.name, p.category,
                   SUM(si.quantity) as total_quantity,
                   SUM(si.total_price) as total_revenue,
                   SUM(si.profit_margin) as total_profit,
                   AVG(si.unit_price) as avg_price
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY p.id
            ORDER BY total_quantity DESC
            LIMIT 20
        ''', (start_date, end_date))
        
        top_products = [dict(row) for row in cursor.fetchall()]
        
        # Sales by category
        cursor.execute('''
            SELECT COALESCE(p.category, 'Sans catégorie') as category,
                   COUNT(DISTINCT si.sale_id) as sales_count,
                   SUM(si.quantity) as total_quantity,
                   SUM(si.total_price) as total_revenue,
                   SUM(si.profit_margin) as total_profit
            FROM sale_items si
            JOIN products p ON si.product_id = p.id  
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY p.category
            ORDER BY total_revenue DESC
        ''', (start_date, end_date))
        
        sales_by_category = [dict(row) for row in cursor.fetchall()]
        
        # Overall statistics
        cursor.execute('''
            SELECT COUNT(*) as total_sales,
                   SUM(total_amount) as total_revenue,
                   AVG(total_amount) as avg_sale_amount,
                   SUM(CASE WHEN is_credit = 1 THEN 1 ELSE 0 END) as credit_sales_count,
                   SUM(CASE WHEN is_credit = 1 THEN total_amount ELSE 0 END) as credit_revenue
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        overall_stats = dict(cursor.fetchone())
        
        # Calculate total profit
        cursor.execute('''
            SELECT SUM(si.profit_margin) as total_profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        profit_result = cursor.fetchone()
        overall_stats['total_profit'] = profit_result[0] if profit_result[0] else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report': {
                'period': {'start': start_date, 'end': end_date, 'group_by': group_by},
                'overall_statistics': overall_stats,
                'sales_by_period': sales_by_period,
                'top_products': top_products,
                'sales_by_category': sales_by_category,
                'generated_at': datetime.now().isoformat(),
                'metadata': report_metadata,
                'note': 'Report shows historical data across all time, which may differ from today\'s sales'
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating sales report: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération du rapport'}), 500

@reports_bp.route('/inventory-report', methods=['GET'])
def generate_inventory_report():
    """Generate inventory status report"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Current inventory status
        cursor.execute('''
            SELECT p.*,
                   (p.purchase_price * p.current_stock) as stock_value,
                   CASE 
                       WHEN p.current_stock <= p.min_stock_alert THEN 'low'
                       WHEN p.current_stock = 0 THEN 'out'
                       ELSE 'normal'
                   END as stock_status
            FROM products p
            WHERE p.is_active = 1
            ORDER BY p.name
        ''')
        
        inventory_items = [dict(row) for row in cursor.fetchall()]
        
        # Inventory summary by category
        cursor.execute('''
            SELECT COALESCE(category, 'Sans catégorie') as category,
                   COUNT(*) as product_count,
                   SUM(current_stock) as total_quantity,
                   SUM(purchase_price * current_stock) as total_value,
                   SUM(CASE WHEN current_stock <= min_stock_alert THEN 1 ELSE 0 END) as low_stock_count
            FROM products
            WHERE is_active = 1
            GROUP BY category
            ORDER BY total_value DESC
        ''')
        
        inventory_by_category = [dict(row) for row in cursor.fetchall()]
        
        # Low stock items
        cursor.execute('''
            SELECT name, current_stock, min_stock_alert, 
                   (purchase_price * current_stock) as stock_value
            FROM products
            WHERE is_active = 1 AND current_stock <= min_stock_alert
            ORDER BY current_stock ASC
        ''')
        
        low_stock_items = [dict(row) for row in cursor.fetchall()]
        
        # Top value items
        cursor.execute('''
            SELECT name, current_stock, purchase_price,
                   (purchase_price * current_stock) as stock_value
            FROM products
            WHERE is_active = 1
            ORDER BY stock_value DESC
            LIMIT 20
        ''')
        
        top_value_items = [dict(row) for row in cursor.fetchall()]
        
        # Overall statistics
        cursor.execute('''
            SELECT COUNT(*) as total_products,
                   SUM(current_stock) as total_quantity,
                   SUM(purchase_price * current_stock) as total_value,
                   COUNT(CASE WHEN current_stock <= min_stock_alert THEN 1 END) as low_stock_count,
                   COUNT(CASE WHEN current_stock = 0 THEN 1 END) as out_of_stock_count
            FROM products
            WHERE is_active = 1
        ''')
        
        overall_stats = dict(cursor.fetchone())
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report': {
                'overall_statistics': overall_stats,
                'inventory_items': inventory_items,
                'inventory_by_category': inventory_by_category,
                'low_stock_items': low_stock_items,
                'top_value_items': top_value_items,
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating inventory report: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération du rapport inventaire'}), 500

@reports_bp.route('/financial-report', methods=['GET'])
def generate_financial_report():
    """Generate comprehensive financial report"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
        end_date = request.args.get('end_date', date.today().isoformat())
        
        # Revenue and profit by period
        cursor.execute('''
            SELECT DATE(s.sale_date) as date,
                   SUM(s.total_amount) as revenue,
                   SUM((SELECT SUM(si.profit_margin) FROM sale_items si WHERE si.sale_id = s.id)) as profit
            FROM sales s
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY DATE(s.sale_date)
            ORDER BY date DESC
        ''', (start_date, end_date))
        
        daily_performance = [dict(row) for row in cursor.fetchall()]
        
        # Expenses by category
        cursor.execute('''
            SELECT category, subcategory,
                   COUNT(*) as count,
                   SUM(amount) as total_amount
            FROM expenses
            WHERE DATE(expense_date) BETWEEN ? AND ?
            GROUP BY category, subcategory
            ORDER BY total_amount DESC
        ''', (start_date, end_date))
        
        expenses_breakdown = [dict(row) for row in cursor.fetchall()]
        
        # Capital entries
        cursor.execute('''
            SELECT DATE(entry_date) as date, source, amount, justification
            FROM capital_entries
            WHERE DATE(entry_date) BETWEEN ? AND ?
            ORDER BY entry_date DESC
        ''', (start_date, end_date))
        
        capital_entries = [dict(row) for row in cursor.fetchall()]
        
        # Cash flow summary
        cursor.execute('''
            SELECT register_date, opening_balance, closing_balance,
                   total_sales, total_expenses, cash_in, cash_out
            FROM cash_register
            WHERE register_date BETWEEN ? AND ?
            ORDER BY register_date DESC
        ''', (start_date, end_date))
        
        cash_flow = [dict(row) for row in cursor.fetchall()]
        
        # Debts summary
        cursor.execute('''
            SELECT 'client' as debt_type, client_name as debtor_name,
                   total_amount, remaining_amount, due_date, status
            FROM client_debts
            WHERE status = 'pending'
            UNION ALL
            SELECT 'supplier' as debt_type, supplier_name as debtor_name,
                   total_amount, remaining_amount, due_date, status
            FROM supplier_debts
            WHERE status = 'pending'
            ORDER BY due_date ASC
        ''')
        
        pending_debts = [dict(row) for row in cursor.fetchall()]
        
        # Calculate totals
        cursor.execute('''
            SELECT 
                (SELECT COALESCE(SUM(amount), 0) FROM capital_entries WHERE DATE(entry_date) BETWEEN ? AND ?) as total_capital,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE DATE(sale_date) BETWEEN ? AND ?) as total_revenue,
                (SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE DATE(expense_date) BETWEEN ? AND ?) as total_expenses,
                (SELECT COALESCE(SUM(remaining_amount), 0) FROM client_debts WHERE status = 'pending') as pending_client_debts,
                (SELECT COALESCE(SUM(remaining_amount), 0) FROM supplier_debts WHERE status = 'pending') as pending_supplier_debts
        ''', (start_date, end_date, start_date, end_date, start_date, end_date))
        
        totals = dict(cursor.fetchone())
        
        # Calculate total profit for the period
        cursor.execute('''
            SELECT COALESCE(SUM(si.profit_margin), 0) as total_profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        profit_result = cursor.fetchone()
        totals['total_profit'] = profit_result[0] if profit_result[0] else 0
        
        # Net income calculation
        totals['net_income'] = totals['total_profit'] - totals['total_expenses']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report': {
                'period': {'start': start_date, 'end': end_date},
                'totals': totals,
                'daily_performance': daily_performance,
                'expenses_breakdown': expenses_breakdown,
                'capital_entries': capital_entries,
                'cash_flow': cash_flow,
                'pending_debts': pending_debts,
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating financial report: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération du rapport financier'}), 500

@reports_bp.route('/audit-log', methods=['GET'])
def get_audit_log():
    """Get user activity audit log (admin only)"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get parameters
        user_id = request.args.get('user_id')
        action_type = request.args.get('action_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        # Build query
        query = '''
            SELECT ual.*, u.username
            FROM user_activity_log ual
            LEFT JOIN users u ON ual.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if user_id:
            query += ' AND ual.user_id = ?'
            params.append(user_id)
        
        if action_type:
            query += ' AND ual.action_type = ?'
            params.append(action_type)
        
        if start_date:
            query += ' AND DATE(ual.created_at) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND DATE(ual.created_at) <= ?'
            params.append(end_date)
        
        query += ' ORDER BY ual.created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        audit_entries = []
        
        for row in cursor.fetchall():
            entry = dict(row)
            # Parse JSON fields
            if entry['old_values']:
                try:
                    entry['old_values'] = json.loads(entry['old_values'])
                except:
                    pass
            if entry['new_values']:
                try:
                    entry['new_values'] = json.loads(entry['new_values'])
                except:
                    pass
            audit_entries.append(entry)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'audit_entries': audit_entries,
            'total_entries': len(audit_entries)
        })
        
    except Exception as e:
        logger.error(f"Error fetching audit log: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération du journal d\'audit'}), 500

@reports_bp.route('/export/<report_type>', methods=['GET'])
def export_report(report_type):
    """Export reports to CSV format"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Prepare CSV data based on report type
        if report_type == 'products':
            cursor.execute('''
                SELECT name, category, supplier, purchase_price, sale_price, 
                       current_stock, min_stock_alert, 
                       (purchase_price * current_stock) as stock_value
                FROM products WHERE is_active = 1
                ORDER BY name
            ''')
            headers = ['Nom', 'Catégorie', 'Fournisseur', 'Prix d\'achat', 'Prix de vente', 
                      'Stock actuel', 'Alerte stock', 'Valeur stock']
            
        elif report_type == 'sales':
            start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
            end_date = request.args.get('end_date', date.today().isoformat())
            
            cursor.execute('''
                SELECT s.id, s.sale_date, s.customer_name, s.total_amount, 
                       s.paid_amount, s.payment_method, s.is_credit,
                       u.username as created_by
                FROM sales s
                LEFT JOIN users u ON s.created_by = u.id
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
                ORDER BY s.sale_date DESC
            ''', (start_date, end_date))
            headers = ['ID', 'Date', 'Client', 'Montant total', 'Montant payé', 
                      'Mode paiement', 'Crédit', 'Créé par']
            
        elif report_type == 'expenses':
            start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
            end_date = request.args.get('end_date', date.today().isoformat())
            
            cursor.execute('''
                SELECT expense_date, category, subcategory, description, amount, 
                       has_receipt, u.username as created_by
                FROM expenses e
                LEFT JOIN users u ON e.created_by = u.id
                WHERE DATE(expense_date) BETWEEN ? AND ?
                ORDER BY expense_date DESC
            ''', (start_date, end_date))
            headers = ['Date', 'Catégorie', 'Sous-catégorie', 'Description',
                      'Montant', 'Reçu', 'Créé par']

        elif report_type == 'customers':
            cursor.execute('''
                SELECT id, name, phone, email, address, created_at
                FROM customers
                WHERE is_active = 1
                ORDER BY name
            ''')
            headers = ['ID', 'Nom', 'Téléphone', 'Email', 'Adresse', 'Créé le']

        elif report_type == 'ai_insights':
            cursor.execute('''
                SELECT prediction_type, product_id, prediction_data, confidence_score, prediction_date
                FROM ai_predictions
                ORDER BY prediction_date DESC
            ''')
            headers = ['Type', 'ID Produit', 'Données', 'Confiance', 'Date']

        elif report_type == 'debts':
            cursor.execute('''
                SELECT 'Client' as type, client_name as name, total_amount,
                       paid_amount, remaining_amount, due_date, status
                FROM client_debts
                UNION ALL
                SELECT 'Fournisseur' as type, supplier_name as name, total_amount,
                       paid_amount, remaining_amount, due_date, status  
                FROM supplier_debts
                ORDER BY due_date ASC
            ''')
            headers = ['Type', 'Nom', 'Montant total', 'Montant payé', 
                      'Montant restant', 'Date échéance', 'Statut']
            
        else:
            return jsonify({'success': False, 'message': 'Type de rapport invalide'}), 400
        
        rows = cursor.fetchall()
        conn.close()
        
        # Create CSV file
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(headers)
        
        # Write data rows
        for row in rows:
            writer.writerow([str(cell) if cell is not None else '' for cell in row])
        
        # Prepare file for download
        output.seek(0)
        csv_data = output.getvalue().encode('utf-8-sig')  # UTF-8 with BOM for Excel
        output.close()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv')
        temp_file.write(csv_data)
        temp_file.close()
        
        filename = f'{report_type}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Log the export (match DatabaseManager.log_user_action signature)
        db_manager.log_user_action(
            session['user_id'],
            'export_report',
            f'Export rapport {report_type}'
        )
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de l\'export'}), 500

@reports_bp.route('/dashboard-analytics', methods=['GET'])
def get_dashboard_analytics():
    """Get analytics data for dashboard charts"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Last 30 days sales trend
        cursor.execute('''
            SELECT DATE(sale_date) as date,
                   COUNT(*) as sales_count,
                   SUM(total_amount) as revenue,
                   SUM((SELECT SUM(profit_margin) FROM sale_items WHERE sale_id = s.id)) as profit
            FROM sales s
            WHERE DATE(sale_date) >= DATE('now', '-30 days')
            GROUP BY DATE(sale_date)
            ORDER BY date
        ''')
        
        sales_trend = [dict(row) for row in cursor.fetchall()]
        
        # Product performance (top 10)
        cursor.execute('''
            SELECT p.name,
                   SUM(si.quantity) as quantity_sold,
                   SUM(si.total_price) as revenue,
                   SUM(si.profit_margin) as profit
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) >= DATE('now', '-30 days')
            GROUP BY p.id
            ORDER BY quantity_sold DESC
            LIMIT 10
        ''')
        
        product_performance = [dict(row) for row in cursor.fetchall()]
        
        # Category sales distribution
        cursor.execute('''
            SELECT COALESCE(p.category, 'Sans catégorie') as category,
                   SUM(si.total_price) as revenue,
                   COUNT(*) as sales_count
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) >= DATE('now', '-30 days')
            GROUP BY p.category
            ORDER BY revenue DESC
        ''')
        
        category_distribution = [dict(row) for row in cursor.fetchall()]
        
        # Monthly comparison (current vs previous month)
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', sale_date) as month,
                COUNT(*) as sales_count,
                SUM(total_amount) as revenue,
                SUM((SELECT SUM(profit_margin) FROM sale_items WHERE sale_id = s.id)) as profit
            FROM sales s
            WHERE strftime('%Y-%m', sale_date) IN (
                strftime('%Y-%m', 'now'),
                strftime('%Y-%m', 'now', '-1 month')
            )
            GROUP BY strftime('%Y-%m', sale_date)
            ORDER BY month DESC
        ''')
        
        monthly_comparison = [dict(row) for row in cursor.fetchall()]
        
        # Stock status overview
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN current_stock = 0 THEN 'Rupture'
                    WHEN current_stock <= min_stock_alert THEN 'Stock faible'
                    ELSE 'Stock normal'
                END as status,
                COUNT(*) as count
            FROM products
            WHERE is_active = 1
            GROUP BY status
        ''')
        
        stock_status = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'analytics': {
                'sales_trend': sales_trend,
                'product_performance': product_performance,
                'category_distribution': category_distribution,
                'monthly_comparison': monthly_comparison,
                'stock_status': stock_status,
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard analytics: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des analyses'}), 500

@reports_bp.route('/sales', methods=['GET'])
def get_sales_report():
    """Alias for sales report endpoint"""
    return generate_sales_report()
