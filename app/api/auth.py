#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication API Blueprint
Handles user authentication, session management, and user operations
"""

from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from db.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
db_manager = DatabaseManager()

@auth_bp.route('/login', methods=['POST'])
def api_login():
    """API endpoint for user login"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('pin'):
        return jsonify({'success': False, 'message': 'Nom d\'utilisateur et PIN requis'}), 400
    
    username = data['username']
    pin = data['pin']
    
    user = db_manager.authenticate_user(username, pin)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['user_role'] = user['role']
        session['language'] = user.get('language', 'fr')
        
        # Log successful login
        db_manager.log_user_action(user['id'], 'login', f'Connexion API réussie pour {username}')
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'language': user['language']
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Nom d\'utilisateur ou PIN incorrect'}), 401

@auth_bp.route('/logout', methods=['POST'])
def api_logout():
    """API endpoint for user logout"""
    if 'user_id' in session:
        db_manager.log_user_action(session['user_id'], 'logout', 'Déconnexion API')
        session.clear()
        return jsonify({'success': True, 'message': 'Déconnexion réussie'})
    return jsonify({'success': False, 'message': 'Aucune session active'}), 400

@auth_bp.route('/status')
def auth_status():
    """Check authentication status"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'role': session['user_role'],
                'language': session.get('language', 'fr')
            }
        })
    return jsonify({'authenticated': False})

@auth_bp.route('/create-user', methods=['POST'])
def create_user():
    """Create new user (admin only)"""
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403
    
    data = request.get_json()
    required_fields = ['username', 'pin', 'role']
    
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Champs requis manquants'}), 400
    
    try:
        user_id = db_manager.create_user(
            username=data['username'],
            pin=data['pin'],
            role=data.get('role', 'employee'),
            language=data.get('language', 'fr')
        )
        
        # Log user creation
        db_manager.log_user_action(
            session['user_id'], 
            'create_user', 
            f'Création utilisateur {data["username"]}',
            'users',
            user_id
        )
        
        return jsonify({'success': True, 'user_id': user_id, 'message': 'Utilisateur créé avec succès'})
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la création de l\'utilisateur'}), 500

@auth_bp.route('/change-pin', methods=['POST'])
def change_pin():
    """Change user PIN"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    
    data = request.get_json()
    if not data or not data.get('current_pin') or not data.get('new_pin'):
        return jsonify({'success': False, 'message': 'PIN actuel et nouveau PIN requis'}), 400
    
    # Verify current PIN
    user = db_manager.authenticate_user(session['username'], data['current_pin'])
    if not user:
        return jsonify({'success': False, 'message': 'PIN actuel incorrect'}), 401
    
    try:
        # Update PIN
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        new_pin_hash = generate_password_hash(data['new_pin'])
        cursor.execute('UPDATE users SET pin_hash = ? WHERE id = ?', (new_pin_hash, session['user_id']))
        conn.commit()
        conn.close()
        
        # Log PIN change
        db_manager.log_user_action(session['user_id'], 'change_pin', 'Changement de PIN')
        
        return jsonify({'success': True, 'message': 'PIN modifié avec succès'})
        
    except Exception as e:
        logger.error(f"Error changing PIN: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors du changement de PIN'}), 500

@auth_bp.route('/users', methods=['GET'])
def list_users():
    """List all users (admin only)"""
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, role, language, created_at, last_login, is_active
            FROM users ORDER BY created_at DESC
        ''')
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'users': users})
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la récupération des utilisateurs'}), 500

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user information (admin only)"""
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Données requises'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get current user data for logging
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'message': "Utilisateur introuvable"}), 404
        old_user = dict(row)
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        if 'username' in data:
            update_fields.append('username = ?')
            values.append(data['username'])
        
        if 'role' in data:
            update_fields.append('role = ?')
            values.append(data['role'])
        
        if 'language' in data:
            update_fields.append('language = ?')
            values.append(data['language'])
        
        if 'is_active' in data:
            update_fields.append('is_active = ?')
            values.append(data['is_active'])
        
        if 'new_pin' in data:
            update_fields.append('pin_hash = ?')
            values.append(generate_password_hash(data['new_pin']))
        
        if update_fields:
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            
            # Log the update
            db_manager.log_user_action(
                session['user_id'],
                'update_user',
                f'Mise à jour utilisateur ID {user_id}',
                'users',
                user_id,
                old_user,
                data
            )
        
        conn.close()
        return jsonify({'success': True, 'message': 'Utilisateur mis à jour avec succès'})
        
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la mise à jour de l\'utilisateur'}), 500

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete/deactivate user (admin only)"""
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403
    
    if user_id == session['user_id']:
        return jsonify({'success': False, 'message': 'Impossible de supprimer votre propre compte'}), 400
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Deactivate instead of delete to preserve data integrity
        cursor.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        # Log the deactivation
        db_manager.log_user_action(
            session['user_id'],
            'deactivate_user',
            f'Désactivation utilisateur ID {user_id}',
            'users',
            user_id
        )
        
        return jsonify({'success': True, 'message': 'Utilisateur désactivé avec succès'})
        
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la désactivation de l\'utilisateur'}), 500
