#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Admin API blueprint for system settings and backups"""

from flask import Blueprint, request, jsonify, session, send_file, make_response
import os
import json
import logging
import traceback
import sys
import platform
import shutil
import flask
from datetime import datetime

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import DatabaseManager from the correct location
from app.data.database import DatabaseManager

# Optional dependency: psutil
try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dep may be absent
    psutil = None  # Fallback handled in endpoint

# Enhanced DatabaseManager to fix app settings issue
class FixedDatabaseManager(DatabaseManager):
    def set_app_settings(self, settings_data):
        """Enhanced version to handle different table structures"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # First check if the app_settings table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings'")
            app_settings_exists = cursor.fetchone() is not None
            
            # Check if the settings table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            settings_exists = cursor.fetchone() is not None
            
            logger.debug(f"Tables: app_settings={app_settings_exists}, settings={settings_exists}")
            
            # Try the app_settings table first (key-value pairs)
            if app_settings_exists:
                try:
                    for key, value in settings_data.items():
                        # Convert complex types to JSON
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value)
                        else:
                            value = str(value)
                            
                        cursor.execute('''
                            REPLACE INTO app_settings (key, value)
                            VALUES (?, ?)
                        ''', (key, value))
                    conn.commit()
                    return {'success': True}
                except Exception as e:
                    logger.warning(f"Failed to update app_settings table: {e}")
                    conn.rollback()
                    # Fall through to try settings table
            
            # Try the settings table (row-based)
            if settings_exists:
                try:
                    # Check if there's a record
                    cursor.execute('SELECT * FROM settings WHERE id = 1')
                    current = cursor.fetchone()
                    
                    if current:
                        # Update existing settings
                        updates = []
                        params = []
                        
                        for key, value in settings_data.items():
                            if key in ['id', 'updated_at']:  # Skip these fields
                                continue
                            
                            # See if column exists in the table
                            cursor.execute(f"PRAGMA table_info(settings)")
                            columns = [row[1] for row in cursor.fetchall()]
                            
                            if key in columns:
                                updates.append(f'{key} = ?')
                                params.append(value)
                            else:
                                logger.warning(f"Column {key} not found in settings table")
                        
                        if updates:
                            # Add updated_at and ID
                            updates.append('updated_at = CURRENT_TIMESTAMP')
                            
                            # Build update query
                            query = f'''
                                UPDATE settings
                                SET {', '.join(updates)}
                                WHERE id = 1
                            '''
                            
                            cursor.execute(query, params)
                            conn.commit()
                            return {'success': True}
                    else:
                        # Create a new settings row
                        # This is more complex as we need to know the schema
                        # Just try to insert default values that we know should exist
                        try:
                            cursor.execute('''
                                INSERT INTO settings (
                                    id, store_name, store_address, store_phone, 
                                    tax_rate, currency, language, updated_at
                                ) VALUES (
                                    1, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
                                )
                            ''', (
                                settings_data.get('store_name', 'Quincaillerie'),
                                settings_data.get('store_address', ''),
                                settings_data.get('store_phone', ''),
                                settings_data.get('tax_rate', 0),
                                settings_data.get('currency', 'MRU'),
                                settings_data.get('language', 'fr')
                            ))
                            conn.commit()
                            return {'success': True}
                        except Exception as inner_e:
                            logger.error(f"Failed to create settings record: {inner_e}")
                            conn.rollback()
                
                except Exception as e:
                    logger.warning(f"Failed to update settings table: {e}")
                    conn.rollback()
            
            # If we got here, both attempts failed
            logger.error("No valid settings table found")
            return {'success': False, 'error': 'No settings table found in database'}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating app settings: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

# Simplified SyncManager (if not available)
class SyncManager:
    def export_offline_data(self):
        try:
            # Create a basic data structure for the backup
            data = {
                'metadata': {
                    'version': '1.0',
                    'date': datetime.now().isoformat(),
                    'type': 'backup'
                },
                'app_settings': {},
                'users': []
            }
            
            # Try to get app settings
            try:
                db = DatabaseManager()
                data['app_settings'] = db.get_app_settings() or {}
                data['users'] = db.get_users() or []
            except Exception as e:
                logger.warning(f"Could not retrieve data for backup: {e}")
            
            return {'success': True, 'data': data}
        except Exception as e:
            logger.error(f"Error in export_offline_data: {e}")
            return {'success': False, 'error': str(e)}

# Configure more detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

admin_bp = Blueprint('admin', __name__)

# Add debug information about the environment
logger.debug(f"Admin blueprint initialized")
logger.debug(f"Python version: {sys.version}")
logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f"Script path: {os.path.abspath(__file__)}")

# Initialize database manager with our fixed version
db_manager = FixedDatabaseManager()
logger.debug(f"Fixed database manager initialized, path: {db_manager.db_path if hasattr(db_manager, 'db_path') else 'unknown'}")

# Initialize sync manager
sync_manager = SyncManager()

# Use absolute path for backups directory - ensure it's in an accessible location
BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backups'))
os.makedirs(BACKUP_DIR, exist_ok=True)
logger.debug(f"Backup directory set to: {BACKUP_DIR}")


def require_admin():
    """Check if the current user is an admin and return an error response if not"""
    logger.debug(f"Session data: {session}")
    
    # Check if session is valid
    if not session:
        logger.warning("Admin access attempt with empty session")
        response = jsonify({'success': False, 'message': 'Session invalide, veuillez vous reconnecter'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 401
    
    # Check if user is logged in
    if 'user_id' not in session:
        logger.warning("Admin access attempt without user_id in session")
        response = jsonify({'success': False, 'message': 'Accès administrateur requis, veuillez vous connecter'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 401
    
    # Check if user is admin
    if session.get('user_role') != 'admin':
        logger.warning(f"Non-admin access attempt: user_id={session.get('user_id')}, role={session.get('user_role')}")
        response = jsonify({'success': False, 'message': 'Accès administrateur requis, privilèges insuffisants'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 403
    
    # All checks passed
    logger.debug(f"Admin access granted for user_id={session.get('user_id')}")
    return None


@admin_bp.route('/settings', methods=['GET', 'POST', 'OPTIONS'])
def app_settings():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
        
    auth_check = require_admin()
    if auth_check:
        return auth_check

    if request.method == 'GET':
        try:
            logger.debug("Getting app settings")
            settings = db_manager.get_app_settings()
            logger.debug(f"Retrieved settings: {settings}")
            response = jsonify({'success': True, 'settings': settings})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error getting app settings: {error_msg}\n{stack_trace}")
            response = jsonify({'success': False, 'message': 'Erreur lors de la récupération des paramètres', 'error': error_msg})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 500

    try:
        # Dump raw request data for debugging
        raw_data = request.data.decode('utf-8') if request.data else None
        logger.debug(f"Raw request data: {raw_data}")
        
        # Try different ways to get the data
        if request.is_json:
            data = request.get_json(silent=True) or {}
            logger.debug(f"JSON data: {data}")
        else:
            try:
                data = json.loads(raw_data) if raw_data else {}
                logger.debug(f"Parsed raw data: {data}")
            except Exception:
                data = request.form.to_dict() or {}
                logger.debug(f"Form data: {data}")
        
        if not data:
            response = jsonify({'success': False, 'message': 'Aucune donnée fournie'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        logger.debug(f"Setting app settings with data: {data}")
        
        # Try direct update first
        try:
            # Direct update with all settings at once
            db_manager.set_app_settings(data)
            db_manager.log_user_action(session['user_id'], 'update_settings', 'Mise à jour des paramètres')
            response = jsonify({'success': True, 'message': 'Paramètres mis à jour avec succès'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as direct_error:
            logger.warning(f"Direct update failed, trying individual updates: {str(direct_error)}")
            # Fall back to individual updates
            success_count = 0
            error_items = []
            
            for key, value in data.items():
                try:
                    db_manager.set_app_settings({key: value})
                    success_count += 1
                except Exception as e:
                    error_items.append(f"{key}: {str(e)}")
                    logger.error(f"Error setting parameter {key}: {str(e)}")
            
            if error_items:
                if success_count > 0:
                    message = f"Certains paramètres ont été mis à jour ({success_count}/{len(data)})"
                    logger.warning(f"{message}. Errors: {', '.join(error_items)}")
                    response = jsonify({'success': True, 'message': message, 'partial': True, 'errors': error_items})
                else:
                    message = "Aucun paramètre n'a pu être mis à jour"
                    logger.error(f"{message}. Errors: {', '.join(error_items)}")
                    response = jsonify({'success': False, 'message': message, 'errors': error_items})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 500
            
            db_manager.log_user_action(session['user_id'], 'update_settings', 'Mise à jour des paramètres (partielle)')
            response = jsonify({'success': True, 'message': 'Paramètres mis à jour avec succès'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Error updating app settings: {error_msg}\n{stack_trace}")
        response = jsonify({'success': False, 'message': 'Erreur lors de la mise à jour des paramètres', 'error': error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@admin_bp.route('/settings/security', methods=['POST', 'OPTIONS'])
def app_settings_security():
    """Update security-related settings: session timeout, max login attempts, audit log, notifications, currency.
    This complements the general /settings endpoint and ensures keys are persisted.
    """
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        data = request.get_json(silent=True) or {}
        # Only keep recognized keys; values are stored in app_settings
        allowed_keys = {
            'session_timeout_minutes',
            'max_login_attempts',
            'audit_log_enabled',
            'email_notifications',
            'currency'
        }
        payload = {k: data[k] for k in data.keys() if k in allowed_keys}
        if not payload:
            response = jsonify({'success': False, 'message': 'Aucune donnée valide fournie'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        db_manager.set_app_settings(payload)
        db_manager.log_user_action(session['user_id'], 'update_security_settings', 'Mise à jour des paramètres de sécurité')
        response = jsonify({'success': True, 'message': 'Paramètres de sécurité mis à jour'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error updating security settings: {error_msg}")
        response = jsonify({'success': False, 'message': error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@admin_bp.route('/backups', methods=['GET', 'POST', 'OPTIONS'])
def backups_list_create():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
        
    auth_check = require_admin()
    if auth_check:
        return auth_check

    if request.method == 'POST':
        try:
            logger.debug("Creating backup...")
            export = sync_manager.export_offline_data()
            if not export.get('success'):
                logger.error(f"Export error: {export.get('error')}")
                response = jsonify({'success': False, 'message': export.get('error', 'Erreur export')})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = os.path.join(BACKUP_DIR, f'backup_{timestamp}.json')
            logger.debug(f"Saving backup to: {path}")
            
            # Make sure the directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(export['data'], f, ensure_ascii=False, indent=2)
            
            db_manager.log_user_action(session['user_id'], 'create_backup', f'Backup {path}')
            response = jsonify({'success': True, 'message': 'Sauvegarde créée avec succès'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error creating backup: {error_msg}\n{stack_trace}")
            response = jsonify({'success': False, 'message': f'Erreur lors de la création de la sauvegarde: {error_msg}'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 500

    try:
        logger.debug(f"Listing backups from: {BACKUP_DIR}")
        backups = []
        if os.path.exists(BACKUP_DIR):
            for fname in sorted(os.listdir(BACKUP_DIR)):
                if fname.endswith('.json'):
                    fpath = os.path.join(BACKUP_DIR, fname)
                    stat = os.stat(fpath)
                    backups.append({
                        'id': fname,
                        'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
                        'size': f"{stat.st_size/1024:.1f} KB",
                        'type': 'Manuel'
                    })
            backups.sort(key=lambda b: b['date'], reverse=True)
        
        logger.debug(f"Found {len(backups)} backups")
        response = jsonify({'success': True, 'backups': backups})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Error listing backups: {error_msg}\n{stack_trace}")
        response = jsonify({'success': False, 'message': f'Erreur lors de la récupération des sauvegardes: {error_msg}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@admin_bp.route('/backups/<backup_id>', methods=['GET', 'DELETE', 'OPTIONS'])
def backup_download_delete(backup_id):
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,DELETE,OPTIONS')
        return response
    
    auth_check = require_admin()
    if auth_check:
        return auth_check

    path = os.path.join(BACKUP_DIR, backup_id)
    logger.debug(f"Accessing backup: {path}")
    
    if not os.path.exists(path):
        response = jsonify({'success': False, 'message': 'Fichier introuvable'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404

    try:
        if request.method == 'DELETE':
            logger.debug(f"Deleting backup: {path}")
            os.remove(path)
            db_manager.log_user_action(session['user_id'], 'delete_backup', backup_id)
            response = jsonify({'success': True, 'message': 'Sauvegarde supprimée avec succès'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        # For download, we don't add CORS headers directly since send_file handles the response
        logger.debug(f"Sending file: {path}")
        response = send_file(path, as_attachment=True)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Error handling backup {backup_id}: {error_msg}\n{stack_trace}")
        response = jsonify({'success': False, 'message': f'Erreur lors du traitement de la sauvegarde: {error_msg}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@admin_bp.route('/backups/restore', methods=['POST', 'OPTIONS'])
def backup_restore():
    """Restore data from a previously exported backup JSON.
    Accepts either multipart/form-data with a file field named 'file' or JSON body with 'data'.
    Restores app settings and users minimally and logs the restore operation.
    """
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        payload = None
        if 'file' in request.files:
            f = request.files['file']
            content = f.read().decode('utf-8')
            payload = json.loads(content)
        else:
            payload = request.get_json(silent=True) or {}
            if 'data' in payload and isinstance(payload['data'], dict):
                payload = payload['data']

        if not payload:
            response = jsonify({'success': False, 'message': 'Aucune donnée de sauvegarde fournie'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        restored = {'settings': False, 'users': 0}

        # Restore settings if present
        settings_data = payload.get('app_settings') or payload.get('settings')
        if isinstance(settings_data, dict):
            try:
                db_manager.set_app_settings(settings_data)
                restored['settings'] = True
            except Exception as e:
                logger.warning(f"Failed to restore settings: {e}")

        # Restore users (non-destructive upsert by username)
        users = payload.get('users')
        if isinstance(users, list):
            for u in users:
                try:
                    if not isinstance(u, dict) or 'username' not in u:
                        continue
                    result = db_manager.upsert_user_by_username(u)
                    if result.get('success'):
                        restored['users'] += 1
                except Exception as e:
                    logger.warning(f"Skipping user restore for {u}: {e}")

        db_manager.log_user_action(session['user_id'], 'restore_backup', 'Restauration des données depuis sauvegarde')
        response = jsonify({'success': True, 'message': 'Restauration terminée', 'restored': restored})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Error restoring backup: {error_msg}\n{stack_trace}")
        response = jsonify({'success': False, 'message': f'Erreur lors de la restauration: {error_msg}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@admin_bp.route('/users', methods=['GET', 'POST', 'OPTIONS'])
def admin_users():
    """List all users or create a new user"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    
    auth_check = require_admin()
    if auth_check:
        return auth_check
        
    if request.method == 'GET':
        try:
            logger.debug("Getting users list")
            users = db_manager.get_users()
            logger.debug(f"Retrieved {len(users)} users")
            response = jsonify({'success': True, 'users': users})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error getting users: {error_msg}\n{stack_trace}")
            response = jsonify({'success': False, 'message': 'Erreur lors de la récupération des utilisateurs'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 500
    
    # POST - Create new user
    try:
        # Dump raw request data for debugging
        raw_data = request.data.decode('utf-8') if request.data else None
        logger.debug(f"Raw request data: {raw_data}")
        
        # Try different ways to get the data
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            try:
                data = json.loads(raw_data) if raw_data else {}
            except Exception:
                data = request.form.to_dict() or {}
        
        logger.debug(f"Processing user creation with data: {data}")
        
        required_fields = ['username', 'pin']
        if not all(field in data for field in required_fields):
            response = jsonify({'success': False, 'message': 'Nom d\'utilisateur et PIN requis'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
            
        # Create user with provided data
        result = db_manager.create_user(data)
        logger.debug(f"User creation result: {result}")
        
        if not result.get('success', False):
            error_msg = result.get('error', 'Erreur lors de la création de l\'utilisateur')
            logger.error(f"User creation error: {error_msg}")
            response = jsonify({'success': False, 'message': error_msg})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
            
        db_manager.log_user_action(session['user_id'], 'create_user', f'Création utilisateur {data["username"]}')
        response = jsonify({'success': True, 'message': 'Utilisateur créé avec succès', 'user_id': result.get('user_id')})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Error creating user: {error_msg}\n{stack_trace}")
        response = jsonify({'success': False, 'message': 'Erreur lors de la création de l\'utilisateur', 'error': error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@admin_bp.route('/users/<int:user_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def admin_user_operations(user_id):
    """Update or delete a user"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'PUT,DELETE,OPTIONS')
        return response
        
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    if request.method == 'PUT':
        try:
            # Dump raw request data for debugging
            raw_data = request.data.decode('utf-8') if request.data else None
            logger.debug(f"Raw request data: {raw_data}")
            
            # Try different ways to get the data
            if request.is_json:
                data = request.get_json(silent=True) or {}
            else:
                try:
                    data = json.loads(raw_data) if raw_data else {}
                except Exception:
                    data = request.form.to_dict() or {}
            
            if not data:
                response = jsonify({'success': False, 'message': 'Aucune donnée fournie'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            
            # Check if trying to modify own role
            if user_id == session.get('user_id') and 'role' in data and data['role'] != 'admin':
                response = jsonify({'success': False, 'message': 'Vous ne pouvez pas rétrograder votre propre rôle'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 403
            
            logger.debug(f"Updating user {user_id} with data: {data}")
            result = db_manager.update_user(user_id, data)
            logger.debug(f"Update result: {result}")
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Erreur lors de la mise à jour de l\'utilisateur')
                logger.error(f"User update error: {error_msg}")
                response = jsonify({'success': False, 'message': error_msg})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
                
            db_manager.log_user_action(session['user_id'], 'update_user', f'Mise à jour utilisateur ID {user_id}')
            response = jsonify({'success': True, 'message': 'Utilisateur mis à jour avec succès'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error updating user: {error_msg}\n{stack_trace}")
            response = jsonify({'success': False, 'message': 'Erreur lors de la mise à jour de l\'utilisateur', 'error': error_msg})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 500
    
    # DELETE
    try:
        # Prevent self-deletion
        if user_id == session.get('user_id'):
            response = jsonify({'success': False, 'message': 'Vous ne pouvez pas supprimer votre propre compte'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 403
        
        logger.debug(f"Deleting user {user_id}")
        result = db_manager.delete_user(user_id)
        logger.debug(f"Delete result: {result}")
        
        if not result.get('success', False):
            error_msg = result.get('error', 'Erreur lors de la suppression de l\'utilisateur')
            logger.error(f"User delete error: {error_msg}")
            response = jsonify({'success': False, 'message': error_msg})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
            
        db_manager.log_user_action(session['user_id'], 'delete_user', f'Suppression utilisateur ID {user_id}')
        response = jsonify({'success': True, 'message': 'Utilisateur supprimé avec succès'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Error deleting user: {error_msg}\n{stack_trace}")
        response = jsonify({'success': False, 'message': 'Erreur lors de la suppression de l\'utilisateur', 'error': error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@admin_bp.route('/debug', methods=['GET'])
def admin_debug():
    """Debug endpoint for admin API"""
    try:
        # Check session status
        session_data = {k: v for k, v in session.items()} if session else {}
        
        # Check database connectivity
        db_status = "OK"
        settings = None
        users = None
        tables = []
        error = None
        
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check settings
            try:
                settings = db_manager.get_app_settings()
            except Exception as e:
                settings = {"error": str(e)}
            
            # Check users
            try:
                users = db_manager.get_users()
                users = [{"id": u["id"], "username": u["username"], "role": u["role"]} for u in users]
            except Exception as e:
                users = {"error": str(e)}
            
            conn.close()
        except Exception as e:
            db_status = f"ERROR: {str(e)}"
            error = str(e)
        
        # Check file system access
        fs_status = "OK"
        backup_dir_exists = False
        backup_dir_writable = False
        backups = []
        
        try:
            backup_dir_exists = os.path.exists(BACKUP_DIR)
            if backup_dir_exists:
                test_file = os.path.join(BACKUP_DIR, "test_write.tmp")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    backup_dir_writable = True
                    os.remove(test_file)
                except Exception:
                    backup_dir_writable = False
                
                backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.json')]
        except Exception as e:
            fs_status = f"ERROR: {str(e)}"
        
        debug_data = {
            "server_time": datetime.now().isoformat(),
            "session": session_data,
            "database": {
                "status": db_status,
                "tables": tables,
                "settings": settings,
                "users": users,
                "error": error
            },
            "filesystem": {
                "status": fs_status,
                "backup_dir": BACKUP_DIR,
                "backup_dir_exists": backup_dir_exists,
                "backup_dir_writable": backup_dir_writable,
                "backups": backups
            },
            "python_version": sys.version,
            "working_directory": os.getcwd(),
        }
        
        response = jsonify({'success': True, 'debug': debug_data})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Error in debug endpoint: {error_msg}\n{stack_trace}")
        response = jsonify({'success': False, 'message': f'Error in debug endpoint: {error_msg}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@admin_bp.route('/logs', methods=['GET', 'OPTIONS'])
def admin_logs():
    """Get application logs"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
    
    try:
        # Check authentication
        # Require admin
        if session.get('user_role') != 'admin':
            response = jsonify({'success': False, 'message': 'Accès administrateur requis'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 403
        
        # Get logs from the logs directory
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        log_files = []
        
        if os.path.exists(logs_dir):
            for file_name in os.listdir(logs_dir):
                if file_name.endswith('.log'):
                    file_path = os.path.join(logs_dir, file_name)
                    try:
                        stat = os.stat(file_path)
                        log_files.append({
                            'name': file_name,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"Error reading log file {file_name}: {e}")
        
        # Get recent log entries (last 100 lines from app.log if it exists)
        recent_logs = []
        app_log_path = os.path.join(logs_dir, 'app.log')
        if os.path.exists(app_log_path):
            try:
                with open(app_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_logs = [line.strip() for line in lines[-100:]]  # Last 100 lines
            except Exception as e:
                logger.warning(f"Error reading app.log: {e}")
        
        response = jsonify({
            'success': True,
            'logs': {
                'files': log_files,
                'recent': recent_logs,
                'logs_dir': logs_dir
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching logs: {error_msg}")
        response = jsonify({'success': False, 'message': f'Error fetching logs: {error_msg}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@admin_bp.route('/system-info', methods=['GET', 'OPTIONS'])
def admin_system_info():
    """Get system information"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
    
    try:
        # Check authentication
        if session.get('user_role') != 'admin':
            response = jsonify({'success': False, 'message': 'Accès administrateur requis'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 403
        
        # Determine disk root
        disk_root = 'C:' if platform.system() == 'Windows' else '/'

        # Get system information with psutil when available; otherwise use limited info
        if psutil is not None:
            system_info = {
                'platform': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'python_version': platform.python_version()
                },
                'cpu': {
                    'cores': psutil.cpu_count(),
                    'cores_logical': psutil.cpu_count(logical=True),
                    'usage_percent': psutil.cpu_percent(interval=1)
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'used': psutil.virtual_memory().used,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage(disk_root).total,
                    'used': psutil.disk_usage(disk_root).used,
                    'free': psutil.disk_usage(disk_root).free,
                    'percent': psutil.disk_usage(disk_root).percent
                },
                'app': {
                    'working_directory': os.getcwd(),
                    'database_path': getattr(db_manager, 'db_path', 'Unknown'),
                    'python_executable': sys.executable,
                    'flask_version': getattr(flask, '__version__', 'Unknown')
                }
            }
        else:
            # Fallback system info without psutil
            du = shutil.disk_usage(disk_root)
            system_info = {
                'platform': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'python_version': platform.python_version()
                },
                'disk': {
                    'total': du.total,
                    'used': du.used,
                    'free': du.free,
                },
                'app': {
                    'working_directory': os.getcwd(),
                    'database_path': getattr(db_manager, 'db_path', 'Unknown'),
                    'python_executable': sys.executable,
                    'flask_version': getattr(flask, '__version__', 'Unknown')
                },
                'note': 'Limited system info available (psutil not installed)'
            }
        
        response = jsonify({
            'success': True,
            'system_info': system_info
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching system info: {error_msg}")
        response = jsonify({'success': False, 'message': f'Error fetching system info: {error_msg}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

