#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Login Script for Inventory Page
This script ensures a user is logged in before redirecting to the inventory page
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
import logging

logger = logging.getLogger(__name__)

# Create a blueprint for our auto-login routes
autologin_bp = Blueprint('autologin', __name__)

@autologin_bp.route('/autologin/inventory')
def autologin_inventory():
    """
    Automatically logs in as admin and redirects to inventory page
    """
    from db.database import DatabaseManager
    
    # If already logged in, just redirect
    if 'user_id' in session:
        logger.info(f"User already logged in as {session.get('username')}, redirecting to inventory")
        return redirect(url_for('inventory'))
    
    # Create database manager and authenticate
    db_manager = DatabaseManager()
    username = 'admin'
    pin = '1234'
    
    logger.info(f"Attempting auto-login as {username}")
    user = db_manager.authenticate_user(username, pin)
    
    if user:
        # Set session variables
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['user_role'] = user['role']
        session['language'] = user.get('language', 'fr')
        
        logger.info(f"Auto-login successful for {username}")
        
        # Log the login
        db_manager.log_user_action(user['id'], 'login', f'Auto-login pour {username}')
        
        # Redirect to inventory page
        return redirect(url_for('inventory'))
    else:
        logger.error(f"Auto-login failed for {username}")
        # Redirect to regular login page with return URL
        return redirect(url_for('login', next=url_for('inventory')))

# Function to register the blueprint
def register_autologin_blueprint(app):
    app.register_blueprint(autologin_bp)
    logger.info("Auto-login blueprint registered")
