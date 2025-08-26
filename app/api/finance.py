#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finance Management API Blueprint
Handles capital tracking, expenses, cash register, and supplier debts
"""

from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from db.database import DatabaseManager
import logging
import os
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

finance_bp = Blueprint('finance', __name__)
db_manager = DatabaseManager()

def require_auth():
    """Check if user is authenticated"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    return None

@finance_bp.route('/capital', methods=['POST'])
def add_capital_entry():
    """Add capital injection entry"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    required_fields = ['amount', 'source', 'entry_date']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Champs requis manquants'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO capital_entries 
            (amount, source, justification, has_receipt, receipt_image, entry_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            float(data['amount']),
            data['source'],
            data.get('justification', ''),
            bool(data.get('has_receipt', False)),
            data.get('receipt_image', ''),
            data['entry_date'],
            session['user_id']
        ))
        
        capital_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the capital entry
        db_manager.log_user_action(
            session['user_id'],
            'add_capital',
            (lambda cur: f"Ajout capital: {data['amount']} {cur} de {data['source']}")((db_manager.get_app_settings().get('currency') or 'MRU')),
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('capital_entries', capital_id, 'insert', data)
        
        return jsonify({
            'success': True,
            'capital_id': capital_id,
            'message': 'Entrée de capital enregistrée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error adding capital entry: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de l\'ajout du capital'}), 500

@finance_bp.route('/capital', methods=['GET'])
def get_capital_entries():
    """Get capital entries with optional filtering"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        source = request.args.get('source')
        
        # Base query
        query = '''
            SELECT ce.*, u.username as created_by_name
            FROM capital_entries ce
            LEFT JOIN users u ON ce.created_by = u.id
            WHERE 1=1
        '''
        params = []
        
        # Add filters
        if start_date:
            query += ' AND DATE(ce.entry_date) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND DATE(ce.entry_date) <= ?'
            params.append(end_date)
        
        if source:
            query += ' AND ce.source LIKE ?'
            params.append(f'%{source}%')
        
        query += ' ORDER BY ce.entry_date DESC, ce.created_at DESC'
        
        cursor.execute(query, params)
        entries = [dict(row) for row in cursor.fetchall()]
        
        # Get total capital invested
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM capital_entries')
        total_capital = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'capital_entries': entries,
            'total_capital': total_capital
        })

    except Exception as e:
        logger.error(f"Error fetching capital entries: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération du capital'}), 500


@finance_bp.route('/capital/<int:entry_id>', methods=['PUT', 'DELETE'])
def modify_capital_entry(entry_id):
    """Update or delete a capital entry"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        if request.method == 'DELETE':
            cursor.execute('DELETE FROM capital_entries WHERE id = ?', (entry_id,))
            conn.commit()
            db_manager.log_user_action(session['user_id'], 'delete_capital', f'Suppression entrée capital #{entry_id}')
            db_manager.add_to_sync_queue('capital_entries', entry_id, 'delete')
            conn.close()
            return jsonify({'success': True})

        data = request.get_json() or {}
        update_fields = []
        values = []

        for field in ['amount', 'source', 'justification', 'entry_date']:
            if field in data:
                update_fields.append(f'{field} = ?')
                values.append(data[field])

        if update_fields:
            values.append(entry_id)
            query = f"UPDATE capital_entries SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            db_manager.log_user_action(session['user_id'], 'update_capital', f'Mise à jour entrée capital #{entry_id}')
            db_manager.add_to_sync_queue('capital_entries', entry_id, 'update', data)

        conn.close()
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error updating capital entry: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la mise à jour'}), 500

@finance_bp.route('/expenses', methods=['POST'])
def add_expense():
    """Add expense entry"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    required_fields = ['amount', 'category', 'description', 'expense_date']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Champs requis manquants'}), 400
    
    if data['category'] not in ['business', 'personal']:
        return jsonify({'success': False, 'message': 'Catégorie invalide'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO expenses 
            (amount, category, subcategory, description, has_receipt, receipt_image, expense_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            float(data['amount']),
            data['category'],
            data.get('subcategory', ''),
            data['description'],
            bool(data.get('has_receipt', False)),
            data.get('receipt_image', ''),
            data['expense_date'],
            session['user_id']
        ))
        
        expense_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the expense
        db_manager.log_user_action(
            session['user_id'],
            'add_expense',
            (lambda cur: f"Ajout dépense {data['category']}: {data['amount']} {cur} - {data['description']}")((db_manager.get_app_settings().get('currency') or 'MRU')),
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('expenses', expense_id, 'insert', data)
        
        return jsonify({
            'success': True,
            'expense_id': expense_id,
            'message': 'Dépense enregistrée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error adding expense: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de l\'ajout de la dépense'}), 500

@finance_bp.route('/expenses', methods=['GET'])
def get_expenses():
    """Get expenses with optional filtering"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        
        # Base query
        query = '''
            SELECT e.*, u.username as created_by_name
            FROM expenses e
            LEFT JOIN users u ON e.created_by = u.id
            WHERE 1=1
        '''
        params = []
        
        # Add filters
        if start_date:
            query += ' AND DATE(e.expense_date) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND DATE(e.expense_date) <= ?'
            params.append(end_date)
        
        if category:
            query += ' AND e.category = ?'
            params.append(category)
        
        if subcategory:
            query += ' AND e.subcategory = ?'
            params.append(subcategory)
        
        query += ' ORDER BY e.expense_date DESC, e.created_at DESC'
        
        cursor.execute(query, params)
        expenses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'expenses': expenses})

    except Exception as e:
        logger.error(f"Error fetching expenses: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des dépenses'}), 500


@finance_bp.route('/expenses/<int:expense_id>', methods=['PUT', 'DELETE'])
def modify_expense(expense_id):
    """Update or delete an expense entry"""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        if request.method == 'DELETE':
            cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
            conn.commit()
            db_manager.log_user_action(session['user_id'], 'delete_expense', f'Suppression dépense #{expense_id}')
            db_manager.add_to_sync_queue('expenses', expense_id, 'delete')
            conn.close()
            return jsonify({'success': True})

        data = request.get_json() or {}
        update_fields = []
        values = []
        for field in ['amount', 'category', 'subcategory', 'description', 'expense_date']:
            if field in data:
                update_fields.append(f'{field} = ?')
                values.append(data[field])

        if update_fields:
            values.append(expense_id)
            query = f"UPDATE expenses SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            db_manager.log_user_action(session['user_id'], 'update_expense', f'Mise à jour dépense #{expense_id}')
            db_manager.add_to_sync_queue('expenses', expense_id, 'update', data)

        conn.close()
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error updating expense: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la mise à jour'}), 500


@finance_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Return combined list of income and expense transactions with optional date filters.

    Query params:
    - start_date: YYYY-MM-DD inclusive
    - end_date: YYYY-MM-DD inclusive
    """
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Build filters for both tables
        cap_where = 'WHERE 1=1'
        exp_where = 'WHERE 1=1'
        params = []
        params2 = []
        if start_date:
            cap_where += ' AND DATE(entry_date) >= ?'
            exp_where += ' AND DATE(expense_date) >= ?'
            params.append(start_date)
            params2.append(start_date)
        if end_date:
            cap_where += ' AND DATE(entry_date) <= ?'
            exp_where += ' AND DATE(expense_date) <= ?'
            params.append(end_date)
            params2.append(end_date)

        # Use UNION ALL with aligned columns and include subcategory + created_at for stable ordering
        sales_where = 'WHERE 1=1'
        params3 = []
        if start_date:
            sales_where += ' AND DATE(sale_date) >= ?'
            params3.append(start_date)
        if end_date:
            sales_where += ' AND DATE(sale_date) <= ?'
            params3.append(end_date)

        query = f'''
            SELECT id, DATE(entry_date) AS date, created_at, amount, source AS description,
                   'income' AS type, 'capital' AS category, 'capital' AS subcategory
            FROM capital_entries
            {cap_where}
            UNION ALL
            SELECT id, DATE(expense_date) AS date, created_at, amount, description,
                   'expense' AS type, category, COALESCE(subcategory, '') AS subcategory
            FROM expenses
            {exp_where}
            UNION ALL
         SELECT id, DATE(sale_date) AS date, created_at, total_amount AS amount,
             'Vente' AS description, 'income' AS type, 'ventes' AS category, '' AS subcategory
            FROM sales
            {sales_where}
            ORDER BY date DESC, created_at DESC
        '''

        cursor.execute(query, params + params2 + params3)
        transactions = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({'success': True, 'transactions': transactions})
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des transactions'}), 500

@finance_bp.route('/cash-register', methods=['POST'])
def create_cash_register():
    """Create or update daily cash register"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    register_date = data.get('register_date', date.today().isoformat())
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check if register already exists for this date
        cursor.execute('SELECT id, is_closed FROM cash_register WHERE register_date = ?', (register_date,))
        existing = cursor.fetchone()
        
        if existing and existing[1]:  # If already closed
            return jsonify({'success': False, 'message': 'La caisse de ce jour est déjà fermée'}), 400
        
        # Calculate totals from sales and expenses for the day
        cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0) FROM sales 
            WHERE DATE(sale_date) = ?
        ''', (register_date,))
        total_sales = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM expenses 
            WHERE DATE(expense_date) = ? AND category = 'business'
        ''', (register_date,))
        total_expenses = cursor.fetchone()[0]
        
        # Get previous day's closing balance as opening balance
        cursor.execute('''
            SELECT closing_balance FROM cash_register 
            WHERE register_date < ? AND is_closed = 1
            ORDER BY register_date DESC LIMIT 1
        ''', (register_date,))
        previous_balance = cursor.fetchone()
        opening_balance = previous_balance[0] if previous_balance else 0
        
        # Calculate cash in/out
        cash_in = float(data.get('cash_in', 0)) + total_sales
        cash_out = float(data.get('cash_out', 0)) + total_expenses
        closing_balance = opening_balance + cash_in - cash_out
        
        if existing:
            # Update existing register
            cursor.execute('''
                UPDATE cash_register 
                SET opening_balance = ?, closing_balance = ?, total_sales = ?, 
                    total_expenses = ?, cash_in = ?, cash_out = ?, notes = ?
                WHERE id = ?
            ''', (opening_balance, closing_balance, total_sales, total_expenses,
                  cash_in, cash_out, data.get('notes', ''), existing[0]))
            register_id = existing[0]
        else:
            # Create new register
            cursor.execute('''
                INSERT INTO cash_register 
                (register_date, opening_balance, closing_balance, total_sales, 
                 total_expenses, cash_in, cash_out, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (register_date, opening_balance, closing_balance, total_sales,
                  total_expenses, cash_in, cash_out, data.get('notes', ''), session['user_id']))
            register_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Log the register operation
        action = 'update_cash_register' if existing else 'create_cash_register'
        db_manager.log_user_action(
            session['user_id'],
            action,
            (lambda cur: f"Caisse {register_date}: solde {closing_balance} {cur}")((db_manager.get_app_settings().get('currency') or 'MRU')),
        )
        
        # Add to sync queue
        operation = 'update' if existing else 'insert'
        db_manager.add_to_sync_queue('cash_register', register_id, operation, {
            'register_date': register_date,
            'closing_balance': closing_balance
        })
        
        return jsonify({
            'success': True,
            'register_id': register_id,
            'closing_balance': closing_balance,
            'message': 'Caisse mise à jour avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error creating cash register: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la création de la caisse'}), 500

@finance_bp.route('/cash-register/close', methods=['POST'])
def close_cash_register():
    """Close daily cash register"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    register_date = data.get('register_date', date.today().isoformat())
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE cash_register 
            SET is_closed = 1, closed_at = CURRENT_TIMESTAMP 
            WHERE register_date = ? AND is_closed = 0
        ''', (register_date,))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'Aucune caisse ouverte trouvée pour cette date'}), 404
        
        conn.commit()
        conn.close()
        
        # Log the closure
        db_manager.log_user_action(
            session['user_id'],
            'close_cash_register',
            f'Fermeture caisse {register_date}'
        )
        
        return jsonify({'success': True, 'message': 'Caisse fermée avec succès'})
        
    except Exception as e:
        logger.error(f"Error closing cash register: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la fermeture de la caisse'}), 500

@finance_bp.route('/cash-register', methods=['GET'])
def get_cash_registers():
    """Get cash register entries"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = '''
            SELECT cr.*, u.username as created_by_name
            FROM cash_register cr
            LEFT JOIN users u ON cr.created_by = u.id
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND cr.register_date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND cr.register_date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY cr.register_date DESC'
        
        cursor.execute(query, params)
        registers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'cash_registers': registers})
        
    except Exception as e:
        logger.error(f"Error fetching cash registers: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des caisses'}), 500

@finance_bp.route('/supplier-debts', methods=['POST'])
def add_supplier_debt():
    """Add supplier debt entry"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    required_fields = ['supplier_name', 'total_amount']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Champs requis manquants'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO supplier_debts 
            (supplier_name, supplier_phone, supplier_address, invoice_reference,
             total_amount, paid_amount, remaining_amount, due_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['supplier_name'],
            data.get('supplier_phone', ''),
            data.get('supplier_address', ''),
            data.get('invoice_reference', ''),
            float(data['total_amount']),
            float(data.get('paid_amount', 0)),
            float(data['total_amount']) - float(data.get('paid_amount', 0)),
            data.get('due_date'),
            session['user_id']
        ))
        
        debt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the debt creation
        db_manager.log_user_action(
            session['user_id'],
            'add_supplier_debt',
            (lambda cur: f"Ajout dette fournisseur: {data['total_amount']} {cur} à {data['supplier_name']}")((db_manager.get_app_settings().get('currency') or 'MRU')),
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('supplier_debts', debt_id, 'insert', data)
        
        return jsonify({
            'success': True,
            'debt_id': debt_id,
            'message': 'Dette fournisseur enregistrée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error adding supplier debt: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de l\'ajout de la dette fournisseur'}), 500

@finance_bp.route('/supplier-debts', methods=['GET'])
def get_supplier_debts():
    """Get supplier debts with optional filtering"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        status = request.args.get('status', 'pending')
        supplier_name = request.args.get('supplier_name')
        
        query = '''
            SELECT sd.*, u.username as created_by_name
            FROM supplier_debts sd
            LEFT JOIN users u ON sd.created_by = u.id
            WHERE sd.status = ?
        '''
        params = [status]
        
        if supplier_name:
            query += ' AND sd.supplier_name LIKE ?'
            params.append(f'%{supplier_name}%')
        
        query += ' ORDER BY sd.due_date ASC'
        
        cursor.execute(query, params)
        debts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'supplier_debts': debts})
        
    except Exception as e:
        logger.error(f"Error fetching supplier debts: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des dettes fournisseurs'}), 500

@finance_bp.route('/supplier-debts/<int:debt_id>/payment', methods=['POST'])
def record_supplier_debt_payment(debt_id):
    """Record payment for a supplier debt"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    if not data or 'payment_amount' not in data:
        return jsonify({'success': False, 'message': 'Montant du paiement requis'}), 400
    
    payment_amount = float(data['payment_amount'])
    if payment_amount <= 0:
        return jsonify({'success': False, 'message': 'Montant du paiement invalide'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get current debt information
        cursor.execute('SELECT * FROM supplier_debts WHERE id = ?', (debt_id,))
        debt = cursor.fetchone()
        if not debt:
            return jsonify({'success': False, 'message': 'Dette non trouvée'}), 404
        
        debt = dict(debt)
        
        if debt['status'] == 'paid':
            return jsonify({'success': False, 'message': 'Cette dette est déjà payée'}), 400
        
        if payment_amount > debt['remaining_amount']:
            return jsonify({'success': False, 'message': 'Montant supérieur à la dette restante'}), 400
        
        # Update debt record
        new_paid_amount = debt['paid_amount'] + payment_amount
        new_remaining_amount = debt['total_amount'] - new_paid_amount
        new_status = 'paid' if new_remaining_amount == 0 else 'pending'
        
        cursor.execute('''
            UPDATE supplier_debts 
            SET paid_amount = ?, remaining_amount = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_paid_amount, new_remaining_amount, new_status, debt_id))
        
        conn.commit()
        conn.close()
        
        # Log the payment
        db_manager.log_user_action(
            session['user_id'],
            'supplier_debt_payment',
            (lambda cur: f"Paiement dette fournisseur: {payment_amount} {cur} à {debt['supplier_name']}")((db_manager.get_app_settings().get('currency') or 'MRU')),
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('supplier_debts', debt_id, 'update', {
            'paid_amount': new_paid_amount,
            'remaining_amount': new_remaining_amount,
            'status': new_status
        })
        
        return jsonify({
            'success': True,
            'new_remaining_amount': new_remaining_amount,
            'new_status': new_status,
            'message': 'Paiement fournisseur enregistré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error recording supplier debt payment: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de l\'enregistrement du paiement'}), 500

@finance_bp.route('/financial-summary', methods=['GET'])
def get_financial_summary():
    """Get comprehensive financial summary"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Total capital invested
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM capital_entries')
        total_capital = cursor.fetchone()[0]
        
        # Total revenue from sales
        cursor.execute('SELECT COALESCE(SUM(total_amount), 0) FROM sales')
        total_revenue = cursor.fetchone()[0]
        
        # Total profit from sales
        cursor.execute('''
            SELECT COALESCE(SUM(profit_margin), 0) 
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
        ''')
        total_profit = cursor.fetchone()[0]
        
        # Total business expenses
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE category = "business"')
        total_business_expenses = cursor.fetchone()[0]
        
        # Total personal expenses
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE category = "personal"')
        total_personal_expenses = cursor.fetchone()[0]
        
        # Current stock value
        cursor.execute('SELECT COALESCE(SUM(purchase_price * current_stock), 0) FROM products WHERE is_active = 1')
        current_stock_value = cursor.fetchone()[0]
        
        # Pending client debts
        cursor.execute('SELECT COALESCE(SUM(remaining_amount), 0) FROM client_debts WHERE status = "pending"')
        pending_client_debts = cursor.fetchone()[0]
        
        # Pending supplier debts
        cursor.execute('SELECT COALESCE(SUM(remaining_amount), 0) FROM supplier_debts WHERE status = "pending"')
        pending_supplier_debts = cursor.fetchone()[0]
        
        # Current cash balance
        cursor.execute('''
            SELECT closing_balance FROM cash_register 
            ORDER BY register_date DESC LIMIT 1
        ''')
        cash_result = cursor.fetchone()
        current_cash_balance = cash_result[0] if cash_result else 0
        
        # Calculate net worth
        net_worth = (total_capital + total_profit - total_business_expenses - 
                    total_personal_expenses + current_stock_value + 
                    pending_client_debts - pending_supplier_debts)
        
        # Capital efficiency score (profit / capital invested)
        capital_efficiency = (total_profit / total_capital * 100) if total_capital > 0 else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'financial_summary': {
                'total_capital': total_capital,
                'total_revenue': total_revenue,
                'total_profit': total_profit,
                'total_business_expenses': total_business_expenses,
                'total_personal_expenses': total_personal_expenses,
                'current_stock_value': current_stock_value,
                'pending_client_debts': pending_client_debts,
                'pending_supplier_debts': pending_supplier_debts,
                'current_cash_balance': current_cash_balance,
                'net_worth': net_worth,
                'capital_efficiency': capital_efficiency
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching financial summary: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération du résumé financier'}), 500


@finance_bp.route('/charts', methods=['GET'])
def get_finance_charts():
    """Return aggregated series for revenue, profit and expenses.
    Accepts either start_date/end_date or period (today, week, month, quarter, year).
    """
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        # Determine date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        period = request.args.get('period')

        today_dt = date.today()
        if not start_date or not end_date:
            # derive from period if provided
            if period == 'today' or not period:
                start = today_dt
                end = today_dt
            elif period == 'week':
                start = today_dt - timedelta(days=7)
                end = today_dt
            elif period == 'month':
                start = today_dt.replace(day=1)
                end = today_dt
            elif period == 'quarter':
                start = (today_dt.replace(day=1) - timedelta(days=90))
                end = today_dt
            elif period == 'year':
                start = date(today_dt.year, 1, 1)
                end = today_dt
            else:
                # default to last 30 days
                start = today_dt - timedelta(days=30)
                end = today_dt
            start_date = start.isoformat()
            end_date = end.isoformat()

        # Decide grouping: by day if range <= 90 days else by month
        try:
            sd = datetime.fromisoformat(start_date).date()
            ed = datetime.fromisoformat(end_date).date()
        except Exception:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else today_dt - timedelta(days=30)
            ed = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else today_dt

        days_range = (ed - sd).days if ed >= sd else 0
        group_monthly = days_range > 90

        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Revenue series
        if group_monthly:
            cursor.execute('''
                SELECT strftime('%Y-%m', sale_date) as period, SUM(total_amount) as revenue
                FROM sales
                WHERE DATE(sale_date) BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', sale_date)
                ORDER BY period
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT DATE(sale_date) as period, SUM(total_amount) as revenue
                FROM sales
                WHERE DATE(sale_date) BETWEEN ? AND ?
                GROUP BY DATE(sale_date)
                ORDER BY period
            ''', (start_date, end_date))
        revenue_rows = {r[0]: r[1] or 0 for r in cursor.fetchall()}

        # Profit series (from sale_items joined to sales)
        if group_monthly:
            cursor.execute('''
                SELECT strftime('%Y-%m', s.sale_date) as period, SUM(si.profit_margin) as profit
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', s.sale_date)
                ORDER BY period
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT DATE(s.sale_date) as period, SUM(si.profit_margin) as profit
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
                GROUP BY DATE(s.sale_date)
                ORDER BY period
            ''', (start_date, end_date))
        profit_rows = {r[0]: r[1] or 0 for r in cursor.fetchall()}

        # Expenses series
        if group_monthly:
            cursor.execute('''
                SELECT strftime('%Y-%m', expense_date) as period, SUM(amount) as expenses
                FROM expenses
                WHERE DATE(expense_date) BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', expense_date)
                ORDER BY period
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT DATE(expense_date) as period, SUM(amount) as expenses
                FROM expenses
                WHERE DATE(expense_date) BETWEEN ? AND ?
                GROUP BY DATE(expense_date)
                ORDER BY period
            ''', (start_date, end_date))
        expense_rows = {r[0]: r[1] or 0 for r in cursor.fetchall()}

        # Expense breakdown by category for doughnut chart
        cursor.execute('''
            SELECT COALESCE(category, 'Sans catégorie') as category, SUM(amount) as total
            FROM expenses
            WHERE DATE(expense_date) BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
            LIMIT 20
        ''', (start_date, end_date))
        expense_breakdown_rows = cursor.fetchall()
        expense_categories = [r[0] for r in expense_breakdown_rows]
        expense_categories_values = [float(r[1] or 0) for r in expense_breakdown_rows]

        conn.close()

        # Build unified labels (sorted)
        labels = sorted(set(list(revenue_rows.keys()) + list(profit_rows.keys()) + list(expense_rows.keys())))

        revenue_series = [float(revenue_rows.get(l, 0) or 0) for l in labels]
        profit_series = [float(profit_rows.get(l, 0) or 0) for l in labels]
        expenses_series = [float(expense_rows.get(l, 0) or 0) for l in labels]

        return jsonify({
            'success': True,
            'charts': {
                'labels': labels,
                'revenue': revenue_series,
                'profit': profit_series,
                'expenses': expenses_series,
                'expense_breakdown': {
                    'categories': expense_categories,
                    'values': expense_categories_values
                },
                'generated_at': datetime.now().isoformat(),
                'start_date': start_date,
                'end_date': end_date
            }
        })

    except Exception as e:
        logger.error(f"Error fetching finance charts: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des données de graphiques'}), 500

@finance_bp.route('/summary', methods=['GET'])
def get_summary():
    """Alias for financial summary endpoint"""
    return get_financial_summary()

@finance_bp.route('/client-debts', methods=['GET'])
def get_client_debts():
    """List client debts with optional filters (status, overdue)."""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        status = (request.args.get('status') or 'pending').lower()
        overdue = (request.args.get('overdue', 'false').lower() == 'true')

        # Base query with computed fields
        query = (
            "SELECT id, client_name, remaining_amount, total_amount, due_date, status, "
            "       CAST(julianday('now') - julianday(due_date) AS INTEGER) AS days_overdue "
            "FROM client_debts WHERE 1=1"
        )
        params = []

        if status in ('pending', 'paid'):
            query += ' AND status = ?'
            params.append(status)

        if overdue:
            query += " AND due_date IS NOT NULL AND DATE(due_date) < DATE('now') AND remaining_amount > 0"

        query += ' ORDER BY due_date ASC NULLS LAST'

        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Aggregate totals
        total_remaining = sum(float(r.get('remaining_amount') or 0) for r in rows)
        count = len(rows)

        return jsonify({'success': True, 'debts': rows, 'count': count, 'total_remaining': total_remaining})
    except Exception as e:
        logger.error(f"Error fetching client debts: {e}")
        return jsonify({'success': False, 'message': "Erreur lors de la récupération des créances"}), 500

@finance_bp.route('/client-debts/<int:debt_id>/status', methods=['PATCH'])
def mark_client_debt_paid(debt_id):
    """Mark a client debt as paid."""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        # Check if debt exists
        cursor.execute('SELECT * FROM client_debts WHERE id = ?', (debt_id,))
        debt = cursor.fetchone()
        if not debt:
            conn.close()
            return jsonify({'success': False, 'message': 'Créance introuvable'}), 404
        # Mark as paid
        cursor.execute('''
            UPDATE client_debts
            SET status = 'paid', remaining_amount = 0, paid_amount = total_amount, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (debt_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Créance marquée comme payée', 'debt_id': debt_id})
    except Exception as e:
        logger.error(f"Error marking client debt as paid: {e}")
        return jsonify({'success': False, 'message': "Erreur lors de la mise à jour de la créance"}), 500
