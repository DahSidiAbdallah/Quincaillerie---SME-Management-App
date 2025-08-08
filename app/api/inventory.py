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

@inventory_bp.route('/stats', methods=['GET'])
def get_inventory_stats():
    """Get inventory statistics"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        # Get inventory stats from database manager
        stats = db_manager.get_inventory_stats()
        
        # Return stats with metadata
        return jsonify({
            'success': True, 
            'stats': stats,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'source': 'inventory/stats',
                'description': 'Current inventory statistics'
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching inventory stats: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des statistiques d\'inventaire'}), 500

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

# filepath: c:\Users\DAH\Downloads\Quincaillerie & SME Management App\app\api\inventory.py

# Add these new API endpoints to your inventory.py file

@inventory_bp.route('/products/<int:product_id>/details', methods=['GET'])
def get_product_details(product_id):
    """Get detailed product info including stock movements and sales"""
    if not require_auth():
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Get product details
        cursor.execute('''
            SELECT * FROM products WHERE id = ? AND is_active = 1
        ''', (product_id,))
        
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Get stock movements
        cursor.execute('''
            SELECT 
                id, movement_type, quantity, reference_id, reference_type, 
                notes, movement_date
            FROM stock_movements
            WHERE product_id = ?
            ORDER BY movement_date DESC
            LIMIT 50
        ''', (product_id,))
        
        movements = []
        for row in cursor.fetchall():
            movements.append(dict(row))
        
        # Get sales history
        cursor.execute('''
            SELECT 
                sd.quantity, sd.unit_price, sd.total_price,
                s.sale_date, s.invoice_number
            FROM sale_details sd
            JOIN sales s ON sd.sale_id = s.id
            WHERE sd.product_id = ? AND s.is_deleted = 0
            ORDER BY s.sale_date DESC
            LIMIT 50
        ''', (product_id,))
        
        sales = []
        for row in cursor.fetchall():
            sales.append(dict(row))
        
        return jsonify({
            'success': True,
            'product': dict(product),
            'movements': movements,
            'sales': sales
        })
    
    except Exception as e:
        logger.error(f"Error getting product details: {e}")
        return jsonify({'success': False, 'message': f"Error: {str(e)}"})
    finally:
        conn.close()

@inventory_bp.route('/adjust-stock', methods=['POST'])
def adjust_stock():
    """Adjust product stock with proper tracking"""
    if not require_auth():
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'})
    
    product_id = data.get('product_id')
    adjustment_type = data.get('adjustment_type')
    quantity = data.get('quantity', 0)
    reason = data.get('reason')
    notes = data.get('notes', '')
    
    if not product_id or not adjustment_type or quantity <= 0:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Get current stock
        cursor.execute('SELECT current_stock FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        current_stock = product['current_stock']
        new_stock = current_stock
        movement_type = 'adjustment'
        
        # Calculate new stock based on adjustment type
        if adjustment_type == 'add':
            new_stock = current_stock + quantity
            movement_type = 'in'
        elif adjustment_type == 'subtract':
            if quantity > current_stock:
                return jsonify({
                    'success': False, 
                    'message': f'Stock insuffisant. Stock actuel: {current_stock}'
                })
            new_stock = current_stock - quantity
            movement_type = 'out'
        elif adjustment_type == 'set':
            if quantity < 0:
                return jsonify({'success': False, 'message': 'La quantité ne peut pas être négative'})
            new_stock = quantity
            
            # Determine movement type based on stock change
            if new_stock > current_stock:
                movement_type = 'in'
                quantity = new_stock - current_stock
            elif new_stock < current_stock:
                movement_type = 'out'
                quantity = current_stock - new_stock
            else:
                # No change in stock
                return jsonify({'success': True, 'message': 'Aucun changement de stock nécessaire'})
        
        # Update product stock
        cursor.execute('''
            UPDATE products
            SET current_stock = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_stock, product_id))
        
        # Record stock movement
        cursor.execute('''
            INSERT INTO stock_movements (
                product_id, movement_type, quantity, reference_type, 
                notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            product_id, 
            movement_type, 
            quantity, 
            reason, 
            notes, 
            session.get('user_id', 0)
        ))
        
        # Log user action
        db_manager.log_user_action(
            user_id=session.get('user_id', 0),
            action_type='stock_adjustment',
            description=f"Ajusté le stock du produit #{product_id}: {movement_type} {quantity} ({reason})"
        )
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': 'Stock ajusté avec succès',
            'new_stock': new_stock
        })
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adjusting stock: {e}")
        return jsonify({'success': False, 'message': f"Error: {str(e)}"})
    finally:
        conn.close()

@inventory_bp.route('/download-import-template', methods=['GET'])
def download_import_template():
    """Provide template file for product import"""
    import io
    import csv
    from flask import Response
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow([
        'name', 'description', 'purchase_price', 'selling_price', 'sku',
        'barcode', 'category', 'supplier', 'initial_stock', 'current_stock',
        'reorder_level', 'min_order_quantity', 'unit'
    ])
    
    # Write example row
    writer.writerow([
        'Marteau', 'Marteau de charpentier', '500', '800', 'MAR-001',
        '123456789', 'Outils', 'Fournisseur XYZ', '10', '10', '5', '1', 'pièce'
    ])
    
    # Return CSV file
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=import_template.csv'}
    )

@inventory_bp.route('/import-products', methods=['POST'])
def import_products():
    """Import products from CSV/Excel file"""
    if not require_auth():
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Aucun fichier trouvé'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'})
    
    # Process based on file extension
    filename = file.filename.lower()
    
    try:
        imported_count = 0
        error_count = 0
        errors = []
        
        if filename.endswith('.csv'):
            # Process CSV
            import csv
            decoded_file = file.stream.read().decode('utf-8')
            csv_reader = csv.DictReader(decoded_file.splitlines())
            imported_count, error_count, errors = process_product_import(csv_reader)
        
        elif filename.endswith('.xlsx'):
            # Process Excel
            import pandas as pd
            df = pd.read_excel(file)
            records = df.to_dict('records')
            imported_count, error_count, errors = process_product_import(records)
        
        else:
            return jsonify({
                'success': False, 
                'message': 'Format de fichier non supporté. Utilisez CSV ou Excel (.xlsx)'
            })
        
        return jsonify({
            'success': True,
            'imported_count': imported_count,
            'error_count': error_count,
            'errors': errors[:10]  # Return only first 10 errors
        })
    
    except Exception as e:
        logger.error(f"Error importing products: {e}")
        return jsonify({'success': False, 'message': f"Erreur d'importation: {str(e)}"})

def process_product_import(records):
    """Process product records for import"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    imported_count = 0
    error_count = 0
    errors = []
    
    try:
        # Start transaction
        conn.execute('BEGIN TRANSACTION')
        
        for idx, record in enumerate(records, 1):
            try:
                # Clean and validate record
                name = str(record.get('name', '')).strip()
                if not name:
                    errors.append(f"Ligne {idx}: Nom du produit manquant")
                    error_count += 1
                    continue
                
                # Try to convert prices to numbers
                try:
                    purchase_price = float(record.get('purchase_price', 0))
                    selling_price = float(record.get('selling_price', 0))
                except ValueError:
                    errors.append(f"Ligne {idx}: Prix invalide")
                    error_count += 1
                    continue
                
                # Check required fields
                if purchase_price <= 0 or selling_price <= 0:
                    errors.append(f"Ligne {idx}: Prix invalides")
                    error_count += 1
                    continue
                
                # Check if product with same SKU already exists
                sku = str(record.get('sku', '')).strip()
                if sku:
                    cursor.execute('SELECT id FROM products WHERE sku = ?', (sku,))
                    if cursor.fetchone():
                        errors.append(f"Ligne {idx}: SKU déjà existant")
                        error_count += 1
                        continue
                
                # Prepare product data
                product_data = {
                    'name': name,
                    'description': str(record.get('description', '')).strip(),
                    'purchase_price': purchase_price,
                    'selling_price': selling_price,
                    'sku': sku,
                    'barcode': str(record.get('barcode', '')).strip(),
                    'category': str(record.get('category', '')).strip(),
                    'supplier': str(record.get('supplier', '')).strip(),
                    'current_stock': int(record.get('current_stock', 0)),
                    'reorder_level': int(record.get('reorder_level', 5)),
                    'min_order_quantity': int(record.get('min_order_quantity', 1)),
                    'created_by': session.get('user_id', 0)
                }
                
                # Insert product
                cursor.execute('''
                    INSERT INTO products (
                        name, description, purchase_price, selling_price, sku, barcode,
                        category, supplier, current_stock, reorder_level, min_order_quantity,
                        created_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    product_data['name'], product_data['description'],
                    product_data['purchase_price'], product_data['selling_price'],
                    product_data['sku'], product_data['barcode'], product_data['category'],
                    product_data['supplier'], product_data['current_stock'],
                    product_data['reorder_level'], product_data['min_order_quantity'],
                    product_data['created_by']
                ))
                
                # Get product ID
                product_id = cursor.lastrowid
                
                # Add stock movement if initial stock > 0
                if product_data['current_stock'] > 0:
                    cursor.execute('''
                        INSERT INTO stock_movements (
                            product_id, movement_type, quantity, reference_type, 
                            notes, created_by
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        product_id, 'in', product_data['current_stock'], 
                        'initial_import', 'Import initial', product_data['created_by']
                    ))
                
                imported_count += 1
            
            except Exception as e:
                error_count += 1
                errors.append(f"Ligne {idx}: {str(e)}")
        
        # Commit transaction if we have any successful imports
        if imported_count > 0:
            conn.commit()
            
            # Log the import action
            db_manager.log_user_action(
                user_id=session.get('user_id', 0),
                action_type='product_import',
                description=f"Importé {imported_count} produits (avec {error_count} erreurs)"
            )
        else:
            conn.rollback()
        
        return imported_count, error_count, errors
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in product import processing: {e}")
        raise
    finally:
        conn.close()

@inventory_bp.route('/export', methods=['GET'])
def export_inventory():
    """Export inventory as CSV using reports blueprint"""
    return redirect(url_for('reports.export_report', report_type='products'))


@inventory_bp.route('/report', methods=['GET'])
def inventory_report_file():
    """Download inventory report (CSV)"""
    return redirect(url_for('reports.export_report', report_type='products'))

@inventory_bp.route('/batch-operation', methods=['POST'])
def batch_product_operation():
    """Perform batch operations on multiple products"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    if not data or 'operation' not in data or 'product_ids' not in data:
        return jsonify({'success': False, 'message': 'Opération et IDs produits requis'}), 400
    
    operation = data['operation']
    product_ids = data['product_ids']
    
    if not isinstance(product_ids, list) or len(product_ids) == 0:
        return jsonify({'success': False, 'message': 'Liste de produits invalide'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Define operations
        operations = {
            'deactivate': {
                'query': 'UPDATE products SET is_active = 0 WHERE id = ?',
                'admin_only': True,
                'log_action': 'deactivate_products',
                'success_msg': 'Produits désactivés avec succès'
            },
            'activate': {
                'query': 'UPDATE products SET is_active = 1 WHERE id = ?',
                'admin_only': True,
                'log_action': 'activate_products',
                'success_msg': 'Produits activés avec succès'
            },
            'update_category': {
                'query': 'UPDATE products SET category = ? WHERE id = ?',
                'admin_only': False,
                'log_action': 'update_products_category',
                'success_msg': 'Catégorie mise à jour avec succès',
                'extra_param': data.get('category', '')
            },
            'update_supplier': {
                'query': 'UPDATE products SET supplier = ? WHERE id = ?',
                'admin_only': False,
                'log_action': 'update_products_supplier',
                'success_msg': 'Fournisseur mis à jour avec succès',
                'extra_param': data.get('supplier', '')
            }
        }
        
        if operation not in operations:
            return jsonify({'success': False, 'message': 'Opération non supportée'}), 400
        
        op_info = operations[operation]
        
        # Check admin permission if required
        if op_info['admin_only'] and session.get('user_role') != 'admin':
            return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403
        
        # Execute operation for each product
        updated_count = 0
        for product_id in product_ids:
            try:
                if 'extra_param' in op_info:
                    cursor.execute(op_info['query'], (op_info['extra_param'], product_id))
                else:
                    cursor.execute(op_info['query'], (product_id,))
                updated_count += cursor.rowcount
            except Exception as e:
                logger.error(f"Error in batch operation for product {product_id}: {e}")
        
        conn.commit()
        
        # Log the action
        db_manager.log_user_action(
            session['user_id'],
            op_info['log_action'],
            f"Opération par lot ({operation}) sur {updated_count} produits",
            'products'
        )
        
        return jsonify({
            'success': True, 
            'updated_count': updated_count,
            'message': op_info['success_msg']
        })
        
    except Exception as e:
        logger.error(f"Error in batch product operation: {e}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500
    finally:
        conn.close()

@inventory_bp.route('/barcode/<barcode>', methods=['GET'])
def lookup_by_barcode(barcode):
    """Look up product by barcode"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, (p.purchase_price * p.current_stock) as stock_value
            FROM products p
            WHERE p.barcode = ? AND p.is_active = 1
        ''', (barcode,))
        
        product = cursor.fetchone()
        conn.close()
        
        if not product:
            return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
            
        return jsonify({'success': True, 'product': dict(product)})
        
    except Exception as e:
        logger.error(f"Error looking up product by barcode: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la recherche par code-barres'}), 500

@inventory_bp.route('/inventory-count', methods=['POST'])
def record_inventory_count():
    """Record physical inventory count/audit"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    data = request.get_json()
    if not data or 'counts' not in data:
        return jsonify({'success': False, 'message': 'Données de comptage requises'}), 400
    
    counts = data['counts']
    count_reference = data.get('reference', f'COUNT-{datetime.now().strftime("%Y%m%d%H%M")}')
