#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sales Management API Blueprint
Handles sales transactions, client debts, and sales operations
"""

from flask import Blueprint, request, jsonify, session
from db.database import DatabaseManager
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

sales_bp = Blueprint('sales', __name__)
db_manager = DatabaseManager()

def require_auth():
    """Check if user is authenticated"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    return None

@sales_bp.route('/sales', methods=['POST'])
def create_sale():
    """Create a new sale transaction"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    required_fields = ['sale_items', 'total_amount', 'paid_amount']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Champs requis manquants'}), 400

    if not data['sale_items'] or len(data['sale_items']) == 0:
        return jsonify({'success': False, 'message': 'Au moins un article est requis'}), 400

    # If credit, require due date
    is_credit = data['paid_amount'] < data['total_amount']
    if is_credit and not data.get('credit_due_date'):
        return jsonify({'success': False, 'message': 'Date d\'échéance requise pour les ventes à crédit'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')
        
        # Validate stock availability for all items first
        for item in data['sale_items']:
            cursor.execute('SELECT current_stock, name FROM products WHERE id = ? AND is_active = 1', 
                          (item['product_id'],))
            product = cursor.fetchone()
            if not product:
                conn.rollback()
                return jsonify({'success': False, 'message': f'Produit ID {item["product_id"]} non trouvé'}), 404
            
            if product[0] < item['quantity']:
                conn.rollback()
                return jsonify({'success': False, 'message': f'Stock insuffisant pour {product[1]}'}), 400
        
        # Create sale record
        is_credit = data['paid_amount'] < data['total_amount']
        sale_date = data.get('sale_date', date.today().isoformat())

        # Determine initial status: credit sales start as 'pending' (en attente), otherwise 'paid'
        status = 'pending' if is_credit else 'paid'
        
        cursor.execute('''
            INSERT INTO sales 
            (sale_date, customer_name, customer_phone, total_amount, paid_amount, 
             payment_method, is_credit, credit_due_date, status, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sale_date,
            data.get('customer_name', ''),
            data.get('customer_phone', ''),
            float(data['total_amount']),
            float(data['paid_amount']),
            data.get('payment_method', 'cash'),
            is_credit,
            data.get('credit_due_date') if is_credit else None,
            status,
            data.get('notes', ''),
            session['user_id']
        ))
        
        sale_id = cursor.lastrowid
        
        # Add sale items and update stock
        total_profit = 0
        low_stock_products = []
        stock_rupture_products = []
        for item in data['sale_items']:
            # Get product details
            cursor.execute('SELECT purchase_price, sale_price, current_stock, name, reorder_level FROM products WHERE id = ?', 
                          (item['product_id'],))
            product = cursor.fetchone()
            
            unit_price = float(item.get('unit_price', product[1]))  # Use provided price or default sale price
            quantity = int(item['quantity'])
            total_price = unit_price * quantity
            profit_margin = (unit_price - product[0]) * quantity
            total_profit += profit_margin
            
            # Insert sale item
            cursor.execute('''
                INSERT INTO sale_items 
                (sale_id, product_id, quantity, unit_price, total_price, profit_margin)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sale_id, item['product_id'], quantity, unit_price, total_price, profit_margin))
            
            # Update product stock
            new_stock = product[2] - quantity
            cursor.execute('UPDATE products SET current_stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                          (new_stock, item['product_id']))
            
            # Add stock movement record
            cursor.execute('''
                INSERT INTO stock_movements 
                (product_id, movement_type, quantity, unit_price, total_amount, reference, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['product_id'],
                'out',
                quantity,
                unit_price,
                total_price,
                f'Vente #{sale_id}',
                f'Vente à {data.get("customer_name", "Client")}',
                session['user_id']
            ))

            # Check for low stock and stock rupture
            reorder_level = product[4] if product[4] is not None else 5
            if new_stock <= reorder_level:
                low_stock_products.append((item['product_id'], product[3], new_stock, reorder_level))
            if new_stock == 0:
                stock_rupture_products.append((item['product_id'], product[3]))
        
        # If it's a credit sale, create debt record
        if is_credit:
            debt_amount = float(data['total_amount']) - float(data['paid_amount'])
            cursor.execute('''
                INSERT INTO client_debts 
                (client_name, client_phone, sale_id, total_amount, paid_amount, 
                 remaining_amount, due_date, created_by, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('customer_name', ''),
                data.get('customer_phone', ''),
                sale_id,
                float(data['total_amount']),
                float(data['paid_amount']),
                debt_amount,
                data.get('credit_due_date'),
                session['user_id'],
                'pending'
            ))

        # Always set status to 'paid' for fully paid sales (not 'completed')
        if not is_credit or float(data['paid_amount']) >= float(data['total_amount']):
            cursor.execute('UPDATE sales SET status = ? WHERE id = ?', ('paid', sale_id))

        conn.commit()

        # --- Automated Notifications ---
        # 1. Sale made
        try:
            db_manager.create_notification(
                type='sale',
                message=f"Nouvelle vente #{sale_id} : {data['total_amount']} à {data.get('customer_name', 'Client')}",
                url=f"/sales/{sale_id}"
            )
        except Exception:
            pass

        # 2. Low stock
        for pid, pname, stock, reorder in low_stock_products:
            try:
                db_manager.create_notification(
                    type='low_stock',
                    message=f"Stock faible: {pname} (reste {stock}, seuil {reorder})",
                    url=f"/products/{pid}"
                )
            except Exception:
                pass

        # 3. Stock rupture
        for pid, pname in stock_rupture_products:
            try:
                db_manager.create_notification(
                    type='stock_rupture',
                    message=f"Rupture de stock: {pname}",
                    url=f"/products/{pid}"
                )
            except Exception:
                pass

        # Log the sale
        db_manager.log_user_action(
            session['user_id'],
            'create_sale',
            # Include sale id in the human-readable log and current currency
            (lambda cur: f'Vente créée #{sale_id}: {data["total_amount"]} {cur} à {data.get("customer_name", "Client")}')( (db_manager.get_app_settings().get('currency') or 'MRU') ),
        )

        # Add to sync queue
        try:
            db_manager.add_to_sync_queue('sales', sale_id, 'insert', data)
        except Exception:
            pass

        conn.close()

        return jsonify({
            'success': True,
            'sale_id': sale_id,
            'total_profit': total_profit,
            'message': 'Vente enregistrée avec succès'
        })
    except Exception as e:
        logger.error(f"Error creating sale: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la création de la vente'}), 500


@sales_bp.route('/create', methods=['POST'])
def create_sale_alias():
    """Alias endpoint to support clients that POST to /api/sales/create (offline sync compatibility).
    Delegates to the main create_sale handler so behavior and logging remain identical.
    """
    return create_sale()

@sales_bp.route('/sales', methods=['GET'])
def get_sales():
    """Get sales with optional filtering"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # --- Auto-update overdue credit sales to 'retard' ---
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT id, customer_name, credit_due_date FROM sales
            WHERE is_credit=1 AND status='pending' AND credit_due_date IS NOT NULL AND credit_due_date < ?
        """, (today,))
        overdue_sales = cursor.fetchall()
        # Update status and send notification for each overdue
        for row in overdue_sales:
            sale_id = row['id'] if isinstance(row, dict) or hasattr(row, '__getitem__') else row[0]
            customer_name = row['customer_name'] if isinstance(row, dict) or hasattr(row, '__getitem__') else row[1]
            due_date = row['credit_due_date'] if isinstance(row, dict) or hasattr(row, '__getitem__') else row[2]
            cursor.execute("UPDATE sales SET status='retard' WHERE id = ?", (sale_id,))
            try:
                db_manager.create_notification(
                    type='payment_delay',
                    message=f"Paiement en retard: Vente #{sale_id} à {customer_name} (échéance {due_date})",
                    url=f"/sales/{sale_id}"
                )
            except Exception:
                pass
        conn.commit()

        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        customer_name = request.args.get('customer_name')
        is_credit = request.args.get('is_credit')
        limit = int(request.args.get('limit', 50))

        # Base query
        query = '''
            SELECT s.*, u.username as created_by_name,
                   (SELECT COALESCE(SUM(si.quantity),0) FROM sale_items si WHERE si.sale_id = s.id) as total_quantity,
                   (SELECT SUM(si.profit_margin) FROM sale_items si WHERE si.sale_id = s.id) as total_profit
            FROM sales s
            LEFT JOIN users u ON s.created_by = u.id
            WHERE 1=1
        '''
        params = []

        # Add filters
        if start_date:
            query += ' AND DATE(s.sale_date) >= ?'
            params.append(start_date)

        if end_date:
            query += ' AND DATE(s.sale_date) <= ?'
            params.append(end_date)

        # No default filter - show all sales if no date specified

        if customer_name:
            query += ' AND s.customer_name LIKE ?'
            params.append(f'%{customer_name}%')

        if is_credit is not None:
            query += ' AND s.is_credit = ?'
            params.append(1 if is_credit.lower() == 'true' else 0)

        query += ' ORDER BY s.created_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        sales = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({'success': True, 'sales': sales})

    except Exception as e:
        logger.error(f"Error fetching sales: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des ventes'}), 500

# Backward-compatible aliases to list sales at the blueprint root
@sales_bp.route('', methods=['GET'])
@sales_bp.route('/', methods=['GET'])
def get_sales_alias():
    """Alias for listing sales when calling /api/sales or /api/sales/"""
    return get_sales()

@sales_bp.route('/sales/<int:sale_id>', methods=['GET'])
def get_sale_details(sale_id):
    """Get detailed information about a specific sale"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get sale information
        cursor.execute('''
            SELECT s.*, u.username as created_by_name
            FROM sales s
            LEFT JOIN users u ON s.created_by = u.id
            WHERE s.id = ?
        ''', (sale_id,))
        
        sale = cursor.fetchone()
        if not sale:
            return jsonify({'success': False, 'message': 'Vente non trouvée'}), 404
        
        # Get sale items
        cursor.execute('''
            SELECT si.*, p.name as product_name, p.purchase_price
            FROM sale_items si
            LEFT JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        ''', (sale_id,))
        
        items = [dict(row) for row in cursor.fetchall()]
        
        # Get debt information if it's a credit sale
        debt_info = None
        if sale['is_credit']:
            cursor.execute('''
                SELECT * FROM client_debts WHERE sale_id = ?
            ''', (sale_id,))
            debt_info = cursor.fetchone()
            if debt_info:
                debt_info = dict(debt_info)
        
        conn.close()
        
        result = dict(sale)
        result['items'] = items
        result['debt_info'] = debt_info
        
        return jsonify({'success': True, 'sale': result})
        
    except Exception as e:
        logger.error(f"Error fetching sale details: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des détails de la vente'}), 500

@sales_bp.route('/stats', methods=['GET'])
def get_sales_stats():
    """Get sales statistics for dashboard"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get today's sales count and amount using exact date
        today_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as amount
            FROM sales
            WHERE DATE(sale_date) = ?
        ''', (today_date,))
        today_sales = cursor.fetchone()
        
        # Get active customers (made purchases in last 30 days)
        cursor.execute('''
            SELECT COUNT(DISTINCT customer_phone) as count
            FROM sales
            WHERE customer_phone != '' AND DATE(sale_date) >= DATE('now', '-30 days')
        ''')
        active_customers = cursor.fetchone()
        
        # Get pending payments from sales table using status field
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM sales
            WHERE status != 'paid' AND (is_credit = 1 OR payment_method = 'credit')
        ''')
        pending_from_sales = cursor.fetchone()
        
        # Get monthly revenue
        cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0) as amount
            FROM sales
            WHERE strftime('%Y-%m', sale_date) = strftime('%Y-%m', 'now')
        ''')
        monthly_revenue = cursor.fetchone()
        
        conn.close()
        
        # Return numeric amounts; frontend will format with the selected currency
        stats = {
            'today_sales': float(today_sales['amount'] or 0),
            'active_customers': active_customers['count'],
            'pending_payments': pending_from_sales['count'] or 0,
            'monthly_revenue': float(monthly_revenue['amount'] or 0)
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Error fetching sales stats: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des statistiques de ventes'}), 500

@sales_bp.route('/sales/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    """Update allowed fields on a sale (admin only)"""
    auth_check = require_auth()
    if auth_check:
        return auth_check


    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Données requises'}), 400

    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Get current sale data
        cursor.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
        old_sale = cursor.fetchone()
        if not old_sale:
            return jsonify({'success': False, 'message': 'Vente non trouvée'}), 404

        old_sale = dict(old_sale)

        # Only allow updating certain fields
        updatable_fields = ['customer_name', 'customer_phone', 'notes', 'credit_due_date']
        update_fields = []
        values = []

        for field in updatable_fields:
            if field in data:
                update_fields.append(f'{field} = ?')
                values.append(data[field])

        if update_fields:
            values.append(sale_id)
            query = f"UPDATE sales SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()

            # Log the update
            db_manager.log_user_action(
                session['user_id'],
                'update_sale',
                f'Mise à jour vente #{sale_id}'
            )

            # Add to sync queue
            try:
                db_manager.add_to_sync_queue('sales', sale_id, 'update', data)
            except Exception:
                pass

        conn.close()
        return jsonify({'success': True, 'message': 'Vente mise à jour avec succès'})

    except Exception as e:
        logger.error(f"Error updating sale: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la mise à jour de la vente'}), 500

@sales_bp.route('/sales/<int:sale_id>', methods=['DELETE'])
def delete_sale(sale_id):
    """Delete a sale and reverse stock movements (admin only)"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403

    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Fetch sale and items
        cursor.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
        sale = cursor.fetchone()
        if not sale:
            return jsonify({'success': False, 'message': 'Vente non trouvée'}), 404

        cursor.execute('SELECT * FROM sale_items WHERE sale_id = ?', (sale_id,))
        items = [dict(row) for row in cursor.fetchall()]

        # Start transaction
        cursor.execute('BEGIN TRANSACTION')


        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            # Fetch sale and items
            cursor.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
            sale = cursor.fetchone()
            if not sale:
                return jsonify({'success': False, 'message': 'Vente non trouvée'}), 404

            cursor.execute('SELECT * FROM sale_items WHERE sale_id = ?', (sale_id,))
            items = [dict(row) for row in cursor.fetchall()]

            # Start transaction
            cursor.execute('BEGIN TRANSACTION')

            # Reverse stock for each item and record movement
            for it in items:
                product_id = it['product_id']
                qty = int(it['quantity'])
                unit_price = float(it.get('unit_price', 0) or 0)
                total_amount = float(it.get('total_price', unit_price * qty))

                # Update stock
                cursor.execute('SELECT current_stock FROM products WHERE id = ?', (product_id,))
                prod = cursor.fetchone()
                if prod is None:
                    conn.rollback()
                    return jsonify({'success': False, 'message': f'Produit {product_id} introuvable pour restauration de stock'}), 404
                new_stock = (prod[0] or 0) + qty
                cursor.execute('UPDATE products SET current_stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_stock, product_id))

                # Stock movement entry
                cursor.execute('''
                    INSERT INTO stock_movements (product_id, movement_type, quantity, unit_price, total_amount, reference, notes, created_by)
                    VALUES (?, 'in', ?, ?, ?, ?, ?, ?)
                ''', (
                    product_id,
                    qty,
                    unit_price,
                    total_amount,
                    f'Annulation vente #{sale_id}',
                    'Restauration du stock suite à suppression de la vente',
                    session['user_id']
                ))

            # Get sale items (prefer new schema sale_items; gracefully fallback to legacy sale_details)
            items = []
            try:
                cursor.execute('''
                    SELECT si.*, p.name as product_name, p.purchase_price
                    FROM sale_items si
                    LEFT JOIN products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                ''', (sale_id,))
                items = [dict(row) for row in cursor.fetchall()]
            except Exception:
                items = []

            # Fallback: some legacy sales store lines in sale_details
            if not items:
                try:
                    cursor.execute('''
                        SELECT sd.*, p.name as product_name, p.purchase_price
                        FROM sale_details sd
                        LEFT JOIN products p ON sd.product_id = p.id
                        WHERE sd.sale_id = ?
                    ''', (sale_id,))
                    legacy_rows = cursor.fetchall()
                    items = []
                    for r in legacy_rows:
                        row = dict(r)
                        qty = row.get('quantity')
                        try:
                            qty = int(qty) if qty is not None else 0
                        except Exception:
                            qty = int(float(qty) if qty is not None else 0)
                        unit_price = row.get('unit_price')
                        try:
                            unit_price = float(unit_price) if unit_price is not None else 0.0
                        except Exception:
                            unit_price = 0.0
                        total_price = row.get('total_price')
                        try:
                            total_price = float(total_price) if total_price is not None else unit_price * qty
                        except Exception:
                            total_price = unit_price * qty
                        row['quantity'] = qty
                        row['unit_price'] = unit_price
                        row['total_price'] = total_price
                        items.append(row)
                except Exception:
                    pass

            # Final safety: if still no items (legacy aggregated sale without detail rows),
            # synthesize a single summary line so the UI isn't empty.
            if not items:
                try:
                    unit = float(sale.get('total_amount') or 0)
                except Exception:
                    unit = 0.0
                items = [{
                    'id': None,
                    'product_id': None,
                    'product_name': 'Vente (non détaillée)',
                    'quantity': 1,
                    'unit_price': unit,
                    'total_price': unit
                }]

            # Delete any associated client debts
            cursor.execute('DELETE FROM client_debts WHERE sale_id = ?', (sale_id,))

            # Finally delete the sale
            cursor.execute('DELETE FROM sales WHERE id = ?', (sale_id,))

            conn.commit()
            conn.close()

            # Log and sync
            db_manager.log_user_action(
                session['user_id'],
                'delete_sale',
                f'Suppression vente #{sale_id} par utilisateur #{session.get("user_id")}'
            )
            try:
                db_manager.add_to_sync_queue('sales', sale_id, 'delete', {})
            except Exception:
                pass

            return jsonify({'success': True, 'message': 'Vente supprimée et stock restauré'})

        except Exception as e:
            logger.error(f"Error deleting sale: {e}")
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression de la vente'}), 500
        overdue_only = request.args.get('overdue_only', 'false').lower() == 'true'
        
        # Base query
        query = '''
            SELECT cd.*, s.sale_date, u.username as created_by_name
            FROM client_debts cd
            LEFT JOIN sales s ON cd.sale_id = s.id
            LEFT JOIN users u ON cd.created_by = u.id
            WHERE cd.status = ?
        '''
        params = [status]
        
        # Add filters
        if client_name:
            query += ' AND cd.client_name LIKE ?'
            params.append(f'%{client_name}%')
        
        if overdue_only:
            query += ' AND cd.due_date < DATE("now")'
        
        query += ' ORDER BY cd.due_date ASC'
        
        cursor.execute(query, params)
        debts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'debts': debts})
        
    except Exception as e:
        logger.error(f"Error fetching client debts: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des dettes'}), 500

@sales_bp.route('/debts/<int:debt_id>/payment', methods=['POST'])
def record_debt_payment(debt_id):
    """Record a payment for a client debt"""
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
        cursor.execute('SELECT * FROM client_debts WHERE id = ?', (debt_id,))
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
            UPDATE client_debts 
            SET paid_amount = ?, remaining_amount = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_paid_amount, new_remaining_amount, new_status, debt_id))

        # If fully paid, ensure the parent sale reflects paid status
        if new_status == 'paid' and debt.get('sale_id'):
            try:
                cursor.execute('''
                    UPDATE sales
                    SET paid_amount = total_amount, is_credit = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (debt['sale_id'],))
            except Exception:
                # If sales schema differs, ignore gracefully
                pass
        
        conn.commit()
        conn.close()
        
        # Log the payment
        db_manager.log_user_action(
            session['user_id'],
            'debt_payment',
            # Use current currency from settings for human-readable log
            (lambda cur: f'Paiement dette: {payment_amount} {cur} de {debt["client_name"]}')( (db_manager.get_app_settings().get('currency') or 'MRU') ),
        )
        
        # Add to sync queue
        try:
            db_manager.add_to_sync_queue('client_debts', debt_id, 'update', {
                'paid_amount': new_paid_amount,
                'remaining_amount': new_remaining_amount,
                'status': new_status
            })
        except Exception:
            pass
        
        return jsonify({
            'success': True,
            'new_remaining_amount': new_remaining_amount,
            'new_status': new_status,
            'message': 'Paiement enregistré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error recording debt payment: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de l\'enregistrement du paiement'}), 500


@sales_bp.route('/sales/<int:sale_id>/status', methods=['PUT'])
def update_sale_status(sale_id):
    """Update sale status. Currently supports marking a credit sale as paid."""
    auth_check = require_auth()
    if auth_check:
        return auth_check

    data = request.get_json(silent=True) or {}
    status = (data.get('status') or '').lower()
    if status not in ('paid',):
        return jsonify({'success': False, 'message': "Statut non supporté. Utilisez 'paid'."}), 400

    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
        sale = cursor.fetchone()
        if not sale:
            return jsonify({'success': False, 'message': 'Vente non trouvée'}), 404

        sale = dict(sale)

        if status == 'paid':
            # If already paid, no-op
            if not sale.get('is_credit') and float(sale.get('paid_amount', 0) or 0) >= float(sale.get('total_amount', 0) or 0):
                conn.close()
                return jsonify({'success': True, 'message': 'La vente est déjà payée'})

            cursor.execute('BEGIN TRANSACTION')
            # Update sale
            cursor.execute('''
                UPDATE sales
                SET paid_amount = total_amount, is_credit = 0, status = 'paid', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (sale_id,))

            # Update any associated debt to paid
            try:
                cursor.execute('''
                    UPDATE client_debts
                    SET paid_amount = total_amount, remaining_amount = 0, status = 'paid', updated_at = CURRENT_TIMESTAMP
                    WHERE sale_id = ?
                ''', (sale_id,))
            except Exception:
                pass

            conn.commit()
            conn.close()

            # Log and sync
            db_manager.log_user_action(
                session['user_id'],
                'update_sale_status',
                f'Marquée payée vente #{sale_id}'
            )
            try:
                db_manager.add_to_sync_queue('sales', sale_id, 'update', {'status': 'paid'})
            except Exception:
                pass

            return jsonify({'success': True, 'message': 'Vente marquée comme payée'})

    except Exception as e:
        logger.error(f"Error updating sale status: {e}")
        # Return error message in response for debugging
        return jsonify({'success': False, 'message': f'Erreur lors de la mise à jour du statut de la vente: {e}'}), 500
    # Fallback (shouldn't reach here)
    return jsonify({'success': False, 'message': 'Requête invalide'}), 400

@sales_bp.route('/statistics', methods=['GET'])
def get_sales_statistics():
    """Get sales statistics for dashboard"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Today's sales
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total,
                   COALESCE(SUM((SELECT SUM(profit_margin) FROM sale_items WHERE sale_id = s.id)), 0) as profit
            FROM sales s WHERE DATE(sale_date) = DATE('now')
        ''')
        today = dict(cursor.fetchone())
        
        # This week's sales
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total,
                   COALESCE(SUM((SELECT SUM(profit_margin) FROM sale_items WHERE sale_id = s.id)), 0) as profit
            FROM sales s WHERE DATE(sale_date) >= DATE('now', '-7 days')
        ''')
        this_week = dict(cursor.fetchone())
        
        # This month's sales
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total,
                   COALESCE(SUM((SELECT SUM(profit_margin) FROM sale_items WHERE sale_id = s.id)), 0) as profit
            FROM sales s WHERE strftime('%Y-%m', sale_date) = strftime('%Y-%m', 'now')
        ''')
        this_month = dict(cursor.fetchone())
        
        # Top selling products this month
        cursor.execute('''
            SELECT p.name, SUM(si.quantity) as total_sold, SUM(si.total_price) as total_revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE strftime('%Y-%m', s.sale_date) = strftime('%Y-%m', 'now')
            GROUP BY p.id, p.name
            ORDER BY total_sold DESC
            LIMIT 10
        ''')
        top_products = [dict(row) for row in cursor.fetchall()]
        
        # Pending debts summary
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(remaining_amount), 0) as total
            FROM client_debts WHERE status = 'pending'
        ''')
        pending_debts = dict(cursor.fetchone())
        
        # Overdue debts
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(remaining_amount), 0) as total
            FROM client_debts WHERE status = 'pending' AND due_date < DATE('now')
        ''')
        overdue_debts = dict(cursor.fetchone())
        
        conn.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'today': today,
                'this_week': this_week,
                'this_month': this_month,
                'top_products': top_products,
                'pending_debts': pending_debts,
                'overdue_debts': overdue_debts
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching sales statistics: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des statistiques'}), 500
