#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inventory Management API Blueprint
Handles product management, stock movements, and inventory operations
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from db.database import DatabaseManager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

inventory_bp = Blueprint('inventory', __name__)
db_manager = DatabaseManager()

def require_auth():
    """Check if user is authenticated"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    return None

@inventory_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        category = request.args.get('category')
        search = request.args.get('search')
        low_stock = request.args.get('low_stock', 'false').lower() == 'true'
        
        # Base query
        query = '''
            SELECT p.*, u.username as created_by_name,
                   (p.purchase_price * p.current_stock) as stock_value
            FROM products p
            LEFT JOIN users u ON p.created_by = u.id
            WHERE p.is_active = 1
        '''
        params = []
        
        # Add filters
        if category:
            query += ' AND p.category = ?'
            params.append(category)
        
        if search:
            query += ' AND (p.name LIKE ? OR p.description LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if low_stock:
            query += ' AND p.current_stock <= p.min_stock_alert'
        
        query += ' ORDER BY p.name ASC'
        
        cursor.execute(query, params)
        products = [dict(row) for row in cursor.fetchall()]

        # Fetch inventory stats for the page
        stats = db_manager.get_inventory_stats()

        conn.close()

        return jsonify({'success': True, 'products': products, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des produits'}), 500

@inventory_bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    required_fields = ['name', 'purchase_price', 'sale_price']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Champs requis manquants'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products 
            (name, description, purchase_price, sale_price, current_stock, 
             min_stock_alert, category, supplier, barcode, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data.get('description', ''),
            float(data['purchase_price']),
            float(data['sale_price']),
            int(data.get('current_stock', 0)),
            int(data.get('min_stock_alert', 5)),
            data.get('category', ''),
            data.get('supplier', ''),
            data.get('barcode', ''),
            session['user_id']
        ))
        
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the creation
        db_manager.log_user_action(
            session['user_id'],
            'create_product',
            f'Création produit: {data["name"]}',
            'products',
            product_id,
            None,
            data
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('products', product_id, 'insert', data)
        
        return jsonify({'success': True, 'product_id': product_id, 'message': 'Produit créé avec succès'})
        
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la création du produit'}), 500

@inventory_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get specific product details"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.username as created_by_name,
                   (p.purchase_price * p.current_stock) as stock_value
            FROM products p
            LEFT JOIN users u ON p.created_by = u.id
            WHERE p.id = ? AND p.is_active = 1
        ''', (product_id,))
        
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
        
        # Get recent stock movements
        cursor.execute('''
            SELECT sm.*, u.username as created_by_name
            FROM stock_movements sm
            LEFT JOIN users u ON sm.created_by = u.id
            WHERE sm.product_id = ?
            ORDER BY sm.created_at DESC LIMIT 10
        ''', (product_id,))
        
        movements = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        result = dict(product)
        result['recent_movements'] = movements
        
        return jsonify({'success': True, 'product': result})
        
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération du produit'}), 500

@inventory_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product information"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Données requises'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get current product data for logging
        cursor.execute('SELECT * FROM products WHERE id = ? AND is_active = 1', (product_id,))
        old_product = cursor.fetchone()
        if not old_product:
            return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
        
        old_product = dict(old_product)
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        updatable_fields = ['name', 'description', 'purchase_price', 'sale_price', 
                           'min_stock_alert', 'category', 'supplier', 'barcode']
        
        for field in updatable_fields:
            if field in data:
                update_fields.append(f'{field} = ?')
                if field in ['purchase_price', 'sale_price']:
                    values.append(float(data[field]))
                elif field == 'min_stock_alert':
                    values.append(int(data[field]))
                else:
                    values.append(data[field])
        
        if update_fields:
            update_fields.append('updated_at = CURRENT_TIMESTAMP')
            values.append(product_id)
            query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            
            # Log the update
            db_manager.log_user_action(
                session['user_id'],
                'update_product',
                f'Mise à jour produit: {old_product["name"]}',
                'products',
                product_id,
                old_product,
                data
            )
            
            # Add to sync queue
            db_manager.add_to_sync_queue('products', product_id, 'update', data)
        
        conn.close()
        return jsonify({'success': True, 'message': 'Produit mis à jour avec succès'})
        
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la mise à jour du produit'}), 500

@inventory_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete/deactivate product"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    # Only admin can delete products
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check if product exists and has no pending operations
        cursor.execute('SELECT name FROM products WHERE id = ? AND is_active = 1', (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
        
        # Deactivate instead of delete to preserve data integrity
        cursor.execute('UPDATE products SET is_active = 0 WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()
        
        # Log the deletion
        db_manager.log_user_action(
            session['user_id'],
            'delete_product',
            f'Suppression produit: {product[0]}',
            'products',
            product_id
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('products', product_id, 'delete')
        
        return jsonify({'success': True, 'message': 'Produit supprimé avec succès'})
        
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la suppression du produit'}), 500

@inventory_bp.route('/stock-movement', methods=['POST'])
def add_stock_movement():
    """Add stock movement (in/out/adjustment)"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    required_fields = ['product_id', 'movement_type', 'quantity']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Champs requis manquants'}), 400
    
    if data['movement_type'] not in ['in', 'out', 'adjustment']:
        return jsonify({'success': False, 'message': 'Type de mouvement invalide'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute('SELECT current_stock, name FROM products WHERE id = ? AND is_active = 1', 
                      (data['product_id'],))
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
        
        current_stock = product[0]
        product_name = product[1]
        quantity = int(data['quantity'])
        
        # Calculate new stock based on movement type
        if data['movement_type'] == 'in':
            new_stock = current_stock + quantity
        elif data['movement_type'] == 'out':
            new_stock = current_stock - quantity
            if new_stock < 0:
                return jsonify({'success': False, 'message': 'Stock insuffisant'}), 400
        else:  # adjustment
            new_stock = quantity
        
        # Add stock movement record
        cursor.execute('''
            INSERT INTO stock_movements 
            (product_id, movement_type, quantity, unit_price, total_amount, reference, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['product_id'],
            data['movement_type'],
            quantity,
            data.get('unit_price'),
            data.get('total_amount'),
            data.get('reference', ''),
            data.get('notes', ''),
            session['user_id']
        ))
        
        movement_id = cursor.lastrowid
        
        # Update product stock
        cursor.execute('UPDATE products SET current_stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                      (new_stock, data['product_id']))
        
        conn.commit()
        conn.close()
        
        # Log the movement
        db_manager.log_user_action(
            session['user_id'],
            'stock_movement',
            f'Mouvement stock {data["movement_type"]}: {product_name} ({quantity})',
            'stock_movements',
            movement_id,
            {'old_stock': current_stock},
            {'new_stock': new_stock, 'movement_data': data}
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('stock_movements', movement_id, 'insert', data)
        
        return jsonify({
            'success': True, 
            'movement_id': movement_id,
            'new_stock': new_stock,
            'message': 'Mouvement de stock enregistré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error adding stock movement: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de l\'enregistrement du mouvement'}), 500

@inventory_bp.route('/stock-movements', methods=['GET'])
def get_stock_movements():
    """Get stock movements with optional filtering"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        product_id = request.args.get('product_id')
        movement_type = request.args.get('movement_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 50))
        
        # Base query
        query = '''
            SELECT sm.*, p.name as product_name, u.username as created_by_name
            FROM stock_movements sm
            LEFT JOIN products p ON sm.product_id = p.id
            LEFT JOIN users u ON sm.created_by = u.id
            WHERE 1=1
        '''
        params = []
        
        # Add filters
        if product_id:
            query += ' AND sm.product_id = ?'
            params.append(product_id)
        
        if movement_type:
            query += ' AND sm.movement_type = ?'
            params.append(movement_type)
        
        if start_date:
            query += ' AND DATE(sm.created_at) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND DATE(sm.created_at) <= ?'
            params.append(end_date)
        
        query += ' ORDER BY sm.created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        movements = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'movements': movements})
        
    except Exception as e:
        logger.error(f"Error fetching stock movements: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des mouvements'}), 500

@inventory_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all product categories"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT category, COUNT(*) as product_count
            FROM products 
            WHERE is_active = 1 AND category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY category ASC
        ''')
        
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'categories': categories})
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des catégories'}), 500

@inventory_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    """Get all suppliers"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT supplier, COUNT(*) as product_count
            FROM products 
            WHERE is_active = 1 AND supplier IS NOT NULL AND supplier != ''
            GROUP BY supplier
            ORDER BY supplier ASC
        ''')
        
        suppliers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'suppliers': suppliers})
        
    except Exception as e:
        logger.error(f"Error fetching suppliers: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des fournisseurs'}), 500

@inventory_bp.route('/low-stock', methods=['GET'])
def get_low_stock_items():
    """Get products with low stock"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, (p.purchase_price * p.current_stock) as stock_value
            FROM products p
            WHERE p.is_active = 1 AND p.current_stock <= p.min_stock_alert
            ORDER BY p.current_stock ASC
        ''')
        
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({'success': True, 'products': products})

    except Exception as e:
        logger.error(f"Error fetching low stock items: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des produits en rupture'}), 500


@inventory_bp.route('/export', methods=['GET'])
def export_inventory():
    """Export inventory as CSV using reports blueprint"""
    return redirect(url_for('reports.export_report', report_type='products'))


@inventory_bp.route('/report', methods=['GET'])
def inventory_report_file():
    """Download inventory report (CSV)"""
    return redirect(url_for('reports.export_report', report_type='products'))
