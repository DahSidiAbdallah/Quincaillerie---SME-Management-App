#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inventory Management API Blueprint
Handles product management, stock operations, and inventory tracking
"""

from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from db.database import DatabaseManager
import logging
import os
from datetime import datetime, date

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
        stock_filter = request.args.get('stock_filter')  # 'low', 'out', 'normal'
        
        # Base query
        query = '''
            SELECT p.*, u.username as created_by_name
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
            query += ' AND (p.name LIKE ? OR p.description LIKE ? OR p.barcode LIKE ?)'
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term])
        
        if stock_filter == 'low':
            query += ' AND p.current_stock <= p.min_stock_alert AND p.current_stock > 0'
        elif stock_filter == 'out':
            query += ' AND p.current_stock = 0'
        elif stock_filter == 'normal':
            query += ' AND p.current_stock > p.min_stock_alert'
        
        query += ' ORDER BY p.name'
        
        cursor.execute(query, params)
        products = [dict(row) for row in cursor.fetchall()]
        
        # Get inventory statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN current_stock > 0 THEN 1 END) as in_stock,
                COUNT(CASE WHEN current_stock <= min_stock_alert AND current_stock > 0 THEN 1 END) as low_stock,
                COUNT(CASE WHEN current_stock = 0 THEN 1 END) as out_of_stock,
                COALESCE(SUM(purchase_price * current_stock), 0) as inventory_value
            FROM products
            WHERE is_active = 1
        ''')
        
        stats = dict(cursor.fetchone())
        conn.close()
        
        return jsonify({
            'success': True,
            'products': products,
            'stats': stats
        })
        
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
            (name, description, purchase_price, sale_price, current_stock, min_stock_alert,
             category, supplier, barcode, created_by)
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
            f'Création produit: {data["name"]}'
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('products', product_id, 'insert', data)
        
        return jsonify({
            'success': True,
            'product_id': product_id,
            'message': 'Produit créé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la création du produit'}), 500

@inventory_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.username as created_by_name
            FROM products p
            LEFT JOIN users u ON p.created_by = u.id
            WHERE p.id = ? AND p.is_active = 1
        ''', (product_id,))
        
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
        
        # Get stock movements for this product
        cursor.execute('''
            SELECT sm.*, u.username as created_by_name
            FROM stock_movements sm
            LEFT JOIN users u ON sm.created_by = u.id
            WHERE sm.product_id = ?
            ORDER BY sm.created_at DESC
            LIMIT 20
        ''', (product_id,))
        
        movements = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        result = dict(product)
        result['stock_movements'] = movements
        
        return jsonify({'success': True, 'product': result})
        
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération du produit'}), 500

@inventory_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
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
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        updatable_fields = ['name', 'description', 'purchase_price', 'sale_price', 
                           'min_stock_alert', 'category', 'supplier', 'barcode']
        
        for field in updatable_fields:
            if field in data:
                update_fields.append(f'{field} = ?')
                values.append(data[field])
        
        if update_fields:
            values.append(product_id)
            query = f"UPDATE products SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            
            # Log the update
            db_manager.log_user_action(
                session['user_id'],
                'update_product',
                f'Mise à jour produit: {data.get("name", old_product["name"])}'
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
    """Soft delete a product (admin only)"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Soft delete (mark as inactive)
        cursor.execute('UPDATE products SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (product_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
        
        conn.commit()
        conn.close()
        
        # Log the deletion
        db_manager.log_user_action(
            session['user_id'],
            'delete_product',
            f'Suppression produit ID: {product_id}'
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('products', product_id, 'delete')
        
        return jsonify({'success': True, 'message': 'Produit supprimé avec succès'})
        
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la suppression du produit'}), 500

@inventory_bp.route('/adjust-stock', methods=['POST'])
def adjust_stock():
    """Adjust product stock levels"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    required_fields = ['product_id', 'adjustment_type', 'quantity']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Champs requis manquants'}), 400
    
    if data['adjustment_type'] not in ['add', 'subtract', 'set']:
        return jsonify({'success': False, 'message': 'Type d\'ajustement invalide'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get current product data
        cursor.execute('SELECT * FROM products WHERE id = ? AND is_active = 1', (data['product_id'],))
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
        
        product = dict(product)
        old_stock = product['current_stock']
        quantity = int(data['quantity'])
        
        # Calculate new stock based on adjustment type
        if data['adjustment_type'] == 'add':
            new_stock = old_stock + quantity
            movement_type = 'in'
            movement_quantity = quantity
        elif data['adjustment_type'] == 'subtract':
            new_stock = max(0, old_stock - quantity)
            movement_type = 'out'
            movement_quantity = quantity
        else:  # set
            new_stock = quantity
            if new_stock > old_stock:
                movement_type = 'in'
                movement_quantity = new_stock - old_stock
            else:
                movement_type = 'out'
                movement_quantity = old_stock - new_stock
        
        # Update product stock
        cursor.execute('UPDATE products SET current_stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                      (new_stock, data['product_id']))
        
        # Record stock movement
        cursor.execute('''
            INSERT INTO stock_movements 
            (product_id, movement_type, quantity, unit_price, total_amount, reference, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['product_id'],
            movement_type,
            movement_quantity,
            product.get('purchase_price', 0),
            movement_quantity * product.get('purchase_price', 0),
            data.get('reference', 'Ajustement manuel'),
            data.get('notes', f'Ajustement {data["adjustment_type"]}: {old_stock} → {new_stock}'),
            session['user_id']
        ))
        
        conn.commit()
        conn.close()
        
        # Log the adjustment
        db_manager.log_user_action(
            session['user_id'],
            'adjust_stock',
            f'Ajustement stock {product["name"]}: {old_stock} → {new_stock}'
        )
        
        # Add to sync queue
        db_manager.add_to_sync_queue('products', data['product_id'], 'update', {
            'current_stock': new_stock
        })
        
        return jsonify({
            'success': True,
            'old_stock': old_stock,
            'new_stock': new_stock,
            'message': 'Stock ajusté avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error adjusting stock: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de l\'ajustement du stock'}), 500

@inventory_bp.route('/stats', methods=['GET'])
def get_inventory_stats():
    """Get inventory statistics"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        stats = db_manager.get_inventory_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Error fetching inventory stats: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des statistiques'}), 500

@inventory_bp.route('/low-stock', methods=['GET'])
def get_low_stock_items():
    """Get products with low stock"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        limit = int(request.args.get('limit', 20))
        items = db_manager.get_low_stock_items(limit=limit)
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        logger.error(f"Error fetching low stock items: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des articles en rupture'}), 500

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
            ORDER BY category
        ''')
        
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'categories': categories})
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des catégories'}), 500

@inventory_bp.route('/stock-movements', methods=['GET'])
def get_stock_movements():
    """Get stock movement history"""
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
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des mouvements de stock'}), 500

@inventory_bp.route('/inventory-count', methods=['POST'])
def inventory_count():
    """Perform inventory count and optionally adjust stock"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    required_fields = ['counts']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Données de comptage requises'}), 400
    
    if not isinstance(data['counts'], list) or len(data['counts']) == 0:
        return jsonify({'success': False, 'message': 'Au moins un produit doit être compté'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')
        
        adjustments_made = []
        total_adjustments = 0
        
        for count_item in data['counts']:
            product_id = count_item.get('product_id')
            counted_qty = int(count_item.get('counted_qty', 0))
            
            if not product_id:
                continue
            
            # Get current stock
            cursor.execute('SELECT current_stock, name FROM products WHERE id = ? AND is_active = 1', (product_id,))
            product = cursor.fetchone()
            if not product:
                continue
            
            current_stock = product[0]
            product_name = product[1]
            difference = counted_qty - current_stock
            
            if difference != 0:
                # Record the adjustment
                adjustments_made.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'old_stock': current_stock,
                    'new_stock': counted_qty,
                    'difference': difference
                })
                
                # Update stock if requested
                if data.get('adjust_stock', True):
                    cursor.execute('UPDATE products SET current_stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                                  (counted_qty, product_id))
                    
                    # Record stock movement
                    movement_type = 'in' if difference > 0 else 'out'
                    cursor.execute('''
                        INSERT INTO stock_movements 
                        (product_id, movement_type, quantity, reference, notes, created_by)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        product_id,
                        movement_type,
                        abs(difference),
                        data.get('reference', 'Comptage inventaire'),
                        f'Comptage: {current_stock} → {counted_qty}',
                        session['user_id']
                    ))
                    
                    total_adjustments += 1
        
        conn.commit()
        conn.close()
        
        # Log the inventory count
        db_manager.log_user_action(
            session['user_id'],
            'inventory_count',
            f'Comptage inventaire: {len(data["counts"])} produits, {total_adjustments} ajustements'
        )
        
        return jsonify({
            'success': True,
            'adjustments': adjustments_made,
            'total_adjustments': total_adjustments,
            'message': f'Comptage terminé: {total_adjustments} ajustements effectués'
        })
        
    except Exception as e:
        logger.error(f"Error performing inventory count: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors du comptage d\'inventaire'}), 500

@inventory_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    """Get list of suppliers"""
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
            ORDER BY supplier
        ''')
        
        suppliers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'suppliers': suppliers})
        
    except Exception as e:
        logger.error(f"Error fetching suppliers: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des fournisseurs'}), 500