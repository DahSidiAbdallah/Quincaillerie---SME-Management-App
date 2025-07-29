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


@customers_bp.route('/customers', methods=['POST'])
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
        return jsonify({'success': True, 'customer_id': customer_id})
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        return jsonify({'success': False, 'error': str(e)})
