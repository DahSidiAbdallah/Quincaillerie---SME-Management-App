#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Customers API blueprint"""

from flask import Blueprint, request, jsonify, session
import logging
from db.database import DatabaseManager

logger = logging.getLogger(__name__)
customers_bp = Blueprint('customers', __name__)

db_manager = DatabaseManager()


def require_auth():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    return None


@customers_bp.route('/customers', methods=['GET'])
@customers_bp.route('/customers/list', methods=['GET'])  # backward-compatible alias
def list_customers():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    try:
        customers = db_manager.get_customers_list()
        return jsonify({'success': True, 'customers': customers})
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        return jsonify({'success': False, 'error': str(e)})


@customers_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    auth_check = require_auth()
    if auth_check:
        return auth_check
    try:
        customer = db_manager.get_customer_by_id(customer_id)
        if customer:
            return jsonify({'success': True, 'customer': customer})
        return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@customers_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    auth_check = require_auth()
    if auth_check:
        return auth_check

    data = request.get_json() or {}
    name = data.get('name')
    phone = data.get('phone', '')
    email = data.get('email', '')
    address = data.get('address', '')

    if not name:
        return jsonify({'success': False, 'error': 'Nom requis'}), 400
    
    # Basic email validation
    if email and '@' not in email:
        return jsonify({'success': False, 'error': 'Format email invalide'}), 400
    
    try:
        success = db_manager.update_customer(customer_id, name, phone, email, address)
        if success:
            db_manager.log_user_action(session['user_id'], 'update_client', f'Mise à jour client ID {customer_id} ({name})')
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Client non trouvé ou aucune modification'}), 404
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@customers_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        success = db_manager.delete_customer(customer_id)
        if success:
            db_manager.log_user_action(session['user_id'], 'delete_client', f'Suppression client ID {customer_id}')
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@customers_bp.route('/customers', methods=['POST'])
@customers_bp.route('/customers/create', methods=['POST'])  # backward-compatible alias
def add_customer():
    auth_check = require_auth()
    if auth_check:
        return auth_check

    data = request.get_json() or {}
    name = data.get('name')
    phone = data.get('phone', '')
    email = data.get('email', '')
    address = data.get('address', '')

    if not name:
        return jsonify({'success': False, 'error': 'Nom requis'}), 400
    try:
        customer_id = db_manager.create_customer(name, phone, email, address)
        if customer_id:
            db_manager.log_user_action(session['user_id'], 'create_client', f'Création client: {name}')
        return jsonify({'success': True, 'customer_id': customer_id})
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        return jsonify({'success': False, 'error': str(e)})
