#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings API for Quincaillerie & SME Management App
Handles user settings, preferences, and profile management
"""

from flask import Blueprint, request, jsonify, session, url_for, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import json
import os

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
settings_bp = Blueprint('settings', __name__)

def init_settings_routes(app, db_manager, MODULES_AVAILABLE, SUPPORTED_LANGUAGES):
    """Initialize settings routes with the Flask app and database manager"""
    
    @settings_bp.route('/api/settings/user-info')
    def user_info():
        """Get current user information including profile, preferences, and activity"""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'success': False, 'error': 'User not authenticated'})
                
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                # Get basic user info
                cursor.execute('''
                    SELECT 
                        id, username, role, language, created_at, last_login
                    FROM users
                    WHERE id = ?
                ''', (user_id,))
                
                user = cursor.fetchone()
                if not user:
                    return jsonify({'success': False, 'error': 'User not found'})
                
                user_data = dict(user)
                
                # Format timestamps
                for key in ['created_at', 'last_login']:
                    if key in user_data and user_data[key]:
                        try:
                            timestamp = datetime.fromisoformat(user_data[key].replace('Z', '+00:00'))
                            user_data[f'{key}_formatted'] = timestamp.strftime('%d/%m/%Y %H:%M')
                        except Exception:
                            user_data[f'{key}_formatted'] = user_data[key]
                
                # Check if user_profiles table exists and get additional profile info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
                has_profiles_table = cursor.fetchone() is not None
                
                if has_profiles_table:
                    cursor.execute('''
                        SELECT first_name, last_name, email, phone, photo_path
                        FROM user_profiles
                        WHERE user_id = ?
                    ''', (user_id,))

                    profile = cursor.fetchone()
                    if profile:
                        prof = dict(profile)
                        # Build a robust photo_url regardless of how path was stored (absolute, static/..., or relative)
                        photo_path = prof.get('photo_path')
                        if photo_path:
                            try:
                                # Normalize slashes
                                pp = str(photo_path).replace('\\', '/')
                                # Resolve static root if available
                                static_root = getattr(current_app, 'static_folder', None)
                                static_root_norm = str(static_root).replace('\\', '/') if static_root else 'static'
                                # Compute a path relative to static/
                                if pp.startswith(static_root_norm):
                                    idx = pp.rfind('static/')
                                    rel = pp[idx + len('static/'):] if idx != -1 else pp
                                elif 'static/' in pp:
                                    rel = pp.split('static/', 1)[1]
                                else:
                                    rel = pp  # assume already relative like uploads/...
                                prof['photo_url'] = url_for('static', filename=rel)
                            except Exception:
                                pass
                        user_data.update(prof)
                
                # Get user preferences if the table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'")
                has_preferences_table = cursor.fetchone() is not None
                
                if has_preferences_table:
                    cursor.execute('''
                        SELECT preferences
                        FROM user_preferences
                        WHERE user_id = ?
                    ''', (user_id,))
                    
                    prefs_row = cursor.fetchone()
                    if prefs_row and prefs_row['preferences']:
                        try:
                            prefs = json.loads(prefs_row['preferences'])
                            user_data['preferences'] = prefs
                        except Exception as e:
                            logger.error(f"Error parsing preferences JSON: {e}")
                
                # Get user activity: detect available timestamp column; be resilient if schema varies
                activities = []
                try:
                    # Determine which time column exists in user_activity_log
                    cursor.execute("PRAGMA table_info(user_activity_log)")
                    cols = [r[1] for r in cursor.fetchall()]
                    time_col = 'action_time' if 'action_time' in cols else ('created_at' if 'created_at' in cols else None)

                    def fetch_activities(col_name: str):
                        try:
                            cursor.execute(f'''
                                SELECT 
                                    action_type, description, {col_name} AS created_at
                                FROM user_activity_log
                                WHERE user_id = ?
                                ORDER BY {col_name} DESC
                                LIMIT 10
                            ''', (user_id,))
                            return cursor.fetchall()
                        except Exception:
                            return []

                    rows = fetch_activities(time_col) if time_col else []

                    for row in rows:
                        activity = dict(row)
                        # Format timestamp
                        if 'created_at' in activity and activity['created_at']:
                            try:
                                timestamp = datetime.fromisoformat(str(activity['created_at']).replace('Z', '+00:00'))
                                activity['formatted_time'] = timestamp.strftime('%d/%m/%Y %H:%M')
                            except Exception:
                                activity['formatted_time'] = activity['created_at']
                        # Provide default status key for UI badge
                        if 'status' not in activity:
                            activity['status'] = 'success'
                        activities.append(activity)
                except Exception as _e:
                    # Non-fatal: leave activities empty if schema differs
                    activities = []
                
                return jsonify({
                    'success': True, 
                    'user': user_data,
                    'activities': activities
                })
            except Exception as e:
                logger.error(f"Error fetching user info: {e}")
                return jsonify({'success': False, 'error': str(e)})
        else:
            # Fallback for minimal mode
            return jsonify({
                'success': True,
                'user': {
                    'username': session.get('username', ''),
                    'role': session.get('user_role', ''),
                    'language': session.get('language', 'fr'),
                    'created_at_formatted': 'Unknown',
                    'last_login_formatted': 'Unknown'
                },
                'activities': []
            })

    @settings_bp.route('/api/settings/upload-photo', methods=['POST'])
    def upload_photo():
        """Upload user profile photo"""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'success': False, 'error': 'User not authenticated'})

                # Language-aware error messaging
                lang = session.get('language', 'fr')
                def msg(no_file=False, bad_type=False):
                    if lang == 'en':
                        if no_file:
                            return 'No file selected. Please choose an image to upload.'
                        if bad_type:
                            return 'Invalid file type. Please upload a JPG, PNG, or GIF image.'
                        return 'An error occurred during upload.'
                    elif lang == 'ar':
                        if no_file:
                            return 'لم يتم اختيار أي ملف. يرجى اختيار صورة للتحميل.'
                        if bad_type:
                            return 'نوع الملف غير صالح. يرجى رفع صورة بتنسيق JPG أو PNG أو GIF.'
                        return 'حدث خطأ أثناء الرفع.'
                    else:  # fr (default)
                        if no_file:
                            return 'Aucun fichier sélectionné. Veuillez choisir une image à téléverser.'
                        if bad_type:
                            return 'Type de fichier invalide. Veuillez téléverser une image JPG, PNG ou GIF.'
                        return 'Une erreur est survenue lors du téléversement.'

                if 'photo' not in request.files:
                    return jsonify({'success': False, 'error': msg(no_file=True), 'code': 'NO_FILE'}), 400
                file = request.files['photo']
                original_name = (file.filename or '').strip()
                if not original_name:
                    return jsonify({'success': False, 'error': msg(no_file=True), 'code': 'NO_FILE'}), 400

                filename = secure_filename(original_name)
                ext = os.path.splitext(filename)[1].lower()
                allowed = {'.jpg', '.jpeg', '.png', '.gif'}
                if ext not in allowed:
                    return jsonify({'success': False, 'error': msg(bad_type=True), 'code': 'BAD_TYPE'}), 400
                # Always save under app static folder to match Flask static route
                static_root = getattr(current_app, 'static_folder', None)
                base_static = static_root if static_root else os.path.join(current_app.root_path, 'static')
                upload_dir = os.path.join(base_static, 'uploads', 'profiles')
                os.makedirs(upload_dir, exist_ok=True)
                new_name = f'user_{user_id}{ext}'
                path = os.path.join(upload_dir, new_name)
                file.save(path)

                # Build stored path (for DB) and URL (for response)
                stored_photo_rel = ('uploads/profiles/' + new_name).replace('\\', '/')
                stored_photo_path = ('static/' + stored_photo_rel).replace('\\', '/')

                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
                exists = cursor.fetchone() is not None
                if exists:
                    cursor.execute('UPDATE user_profiles SET photo_path = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (stored_photo_path, user_id))
                else:
                    cursor.execute('INSERT INTO user_profiles (user_id, photo_path) VALUES (?, ?)', (user_id, stored_photo_path))
                conn.commit(); conn.close()

                db_manager.log_user_action(user_id, 'upload_photo', 'Mise à jour photo profil')
                # Build photo URL from stored relative path
                try:
                    photo_url = url_for('static', filename=stored_photo_rel)
                except Exception:
                    photo_url = None

                return jsonify({'success': True, 'photo_url': photo_url})
            except Exception as e:
                logger.error(f"Error uploading photo: {e}")
                return jsonify({'success': False, 'error': str(e)})
        else:
            return jsonify({'success': False, 'error': 'Cette fonctionnalité n\'est pas disponible en mode minimal'})

    @settings_bp.route('/api/settings/update-profile', methods=['POST'])
    def update_profile():
        """Update user profile information"""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                data = request.get_json()
                user_id = session.get('user_id')
                
                if not user_id:
                    return jsonify({'success': False, 'error': 'User not authenticated'})
                
                # Prepare profile data
                profile_data = {
                    'first_name': data.get('first_name', ''),
                    'last_name': data.get('last_name', ''),
                    'email': data.get('email', ''),
                    'phone': data.get('phone', ''),
                    'photo_path': data.get('photo_path', '')
                }
                
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                # Check if user_profiles table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
                has_profiles_table = cursor.fetchone() is not None
                
                if not has_profiles_table:
                    # Create user_profiles table if it doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_profiles (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            first_name TEXT,
                            last_name TEXT,
                            email TEXT,
                            phone TEXT,
                            photo_path TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    ''')
                    conn.commit()
                
                # Check if profile exists for this user
                cursor.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
                profile_exists = cursor.fetchone() is not None
                
                if profile_exists:
                    # Update existing profile
                    cursor.execute('''
                        UPDATE user_profiles
                        SET first_name = ?, last_name = ?, email = ?, phone = ?, photo_path = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (
                        profile_data['first_name'],
                        profile_data['last_name'],
                        profile_data['email'],
                        profile_data['phone'],
                        profile_data['photo_path'],
                        user_id
                    ))
                else:
                    # Insert new profile
                    cursor.execute('''
                        INSERT INTO user_profiles (user_id, first_name, last_name, email, phone, photo_path)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        profile_data['first_name'],
                        profile_data['last_name'],
                        profile_data['email'],
                        profile_data['phone'],
                        profile_data['photo_path']
                    ))
                
                conn.commit()
                
                # Log the action
                db_manager.log_user_action(user_id, 'update_profile', 'Mise à jour du profil utilisateur')
                
                return jsonify({
                    'success': True, 
                    'message': 'Profil mis à jour avec succès'
                })
            except Exception as e:
                logger.error(f"Error updating profile: {e}")
                return jsonify({'success': False, 'error': str(e)})
        else:
            return jsonify({
                'success': False,
                'error': 'Cette fonctionnalité n\'est pas disponible en mode minimal'
            })
    
    @settings_bp.route('/api/settings/update-language', methods=['POST'])
    def update_language():
        """Update user language preference"""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                data = request.get_json()
                language = data.get('language')
                
                if not language or language not in SUPPORTED_LANGUAGES:
                    return jsonify({'success': False, 'error': 'Langue invalide'})
                
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'success': False, 'error': 'Utilisateur non authentifié'})
                
                # Update user language in database
                db_manager.update_user_language(user_id, language)
                
                # Update session
                session['language'] = language
                
                # Log the action
                db_manager.log_user_action(user_id, 'update_language', f"Changement de langue vers {SUPPORTED_LANGUAGES[language]}")
                
                return jsonify({
                    'success': True, 
                    'message': f'Langue mise à jour vers {SUPPORTED_LANGUAGES[language]}'
                })
            except Exception as e:
                logger.error(f"Error updating language: {e}")
                return jsonify({'success': False, 'error': str(e)})
        else:
            # Update session even in minimal mode
            language = request.get_json().get('language')
            if language in SUPPORTED_LANGUAGES:
                session['language'] = language
                return jsonify({
                    'success': True, 
                    'message': f'Langue mise à jour vers {SUPPORTED_LANGUAGES[language]}'
                })
            else:
                return jsonify({'success': False, 'error': 'Langue invalide'})
    
    @settings_bp.route('/api/settings/update-preferences', methods=['POST'])
    def update_preferences():
        """Update user preferences"""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                data = request.get_json()
                user_id = session.get('user_id')
                
                if not user_id:
                    return jsonify({'success': False, 'error': 'Utilisateur non authentifié'})
                
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                # Check if user_preferences table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'")
                has_preferences_table = cursor.fetchone() is not None
                
                if not has_preferences_table:
                    # Create user_preferences table if it doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_preferences (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            preferences TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    ''')
                    conn.commit()
                
                # Serialize preferences to JSON
                preferences_json = json.dumps(data)
                
                # Check if preferences exist for this user
                cursor.execute('SELECT id FROM user_preferences WHERE user_id = ?', (user_id,))
                preferences_exist = cursor.fetchone() is not None
                
                if preferences_exist:
                    # Update existing preferences
                    cursor.execute('''
                        UPDATE user_preferences 
                        SET preferences = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (preferences_json, user_id))
                else:
                    # Insert new preferences
                    cursor.execute('''
                        INSERT INTO user_preferences (user_id, preferences)
                        VALUES (?, ?)
                    ''', (user_id, preferences_json))
                
                conn.commit()
                
                # Check if language was changed
                reload_required = False
                if 'language' in data and data['language'] != session.get('language'):
                    # Update language in users table
                    db_manager.update_user_language(user_id, data['language'])
                    # Update session
                    session['language'] = data['language']
                    reload_required = True
                
                # Log the action
                db_manager.log_user_action(user_id, 'update_preferences', 'Mise à jour des préférences utilisateur')
                
                return jsonify({
                    'success': True, 
                    'message': 'Préférences mises à jour avec succès',
                    'reload_required': reload_required
                })
            except Exception as e:
                logger.error(f"Error updating preferences: {e}")
                return jsonify({'success': False, 'error': str(e)})
        else:
            return jsonify({
                'success': False,
                'error': 'Cette fonctionnalité n\'est pas disponible en mode minimal'
            })
    
    @settings_bp.route('/api/settings/update-pin', methods=['POST'])
    def update_pin():
        """Update user PIN"""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                data = request.get_json()
                current_pin = data.get('current_pin')
                new_pin = data.get('new_pin')
                
                if not current_pin or not new_pin:
                    return jsonify({'success': False, 'error': 'PIN actuel et nouveau PIN requis'})
                
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'success': False, 'error': 'Utilisateur non authentifié'})
                
                # Verify current PIN
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('SELECT pin_hash FROM users WHERE id = ?', (user_id,))
                user = cursor.fetchone()
                
                if not user or not check_password_hash(user['pin_hash'], current_pin):
                    return jsonify({'success': False, 'error': 'PIN actuel incorrect'})
                
                # Update PIN
                new_pin_hash = generate_password_hash(new_pin)
                cursor.execute('UPDATE users SET pin_hash = ? WHERE id = ?', (new_pin_hash, user_id))
                conn.commit()
                
                # Log the action
                db_manager.log_user_action(user_id, 'update_pin', 'Changement du PIN utilisateur')
                
                return jsonify({
                    'success': True, 
                    'message': 'PIN mis à jour avec succès'
                })
            except Exception as e:
                logger.error(f"Error updating PIN: {e}")
                return jsonify({'success': False, 'error': str(e)})
        else:
            return jsonify({
                'success': False,
                'error': 'Cette fonctionnalité n\'est pas disponible en mode minimal'
            })
    
    @settings_bp.route('/api/settings/update-notifications', methods=['POST'])
    def update_notifications():
        """Update notification preferences"""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                data = request.get_json()
                user_id = session.get('user_id')
                
                if not user_id:
                    return jsonify({'success': False, 'error': 'Utilisateur non authentifié'})
                
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                # Check if notification_preferences table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_preferences'")
                has_notifications_table = cursor.fetchone() is not None
                
                if not has_notifications_table:
                    # Create notification_preferences table if it doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS notification_preferences (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            preferences TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    ''')
                    conn.commit()
                
                # Serialize notification preferences to JSON
                notifications_json = json.dumps(data)
                
                # Check if notification preferences exist for this user
                cursor.execute('SELECT id FROM notification_preferences WHERE user_id = ?', (user_id,))
                notifications_exist = cursor.fetchone() is not None
                
                if notifications_exist:
                    # Update existing notification preferences
                    cursor.execute('''
                        UPDATE notification_preferences 
                        SET preferences = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (notifications_json, user_id))
                else:
                    # Insert new notification preferences
                    cursor.execute('''
                        INSERT INTO notification_preferences (user_id, preferences)
                        VALUES (?, ?)
                    ''', (user_id, notifications_json))
                
                conn.commit()
                
                # Log the action
                db_manager.log_user_action(user_id, 'update_notifications', 'Mise à jour des préférences de notification')
                
                return jsonify({
                    'success': True, 
                    'message': 'Préférences de notification mises à jour avec succès'
                })
            except Exception as e:
                logger.error(f"Error updating notification preferences: {e}")
                return jsonify({'success': False, 'error': str(e)})
        else:
            return jsonify({
                'success': False,
                'error': 'Cette fonctionnalité n\'est pas disponible en mode minimal'
            })
    
    @settings_bp.route('/api/settings/preferences', methods=['GET'])
    def get_preferences():
        """Get user preferences"""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'success': False, 'error': 'Utilisateur non authentifié'})
                
                # Get user settings from database
                settings = db_manager.get_app_settings()
                
                # Default preferences (app-level)
                preferences = {
                    'language': settings.get('language', 'fr'),
                    'currency': settings.get('currency', 'MRU'),
                    'decimal_places': settings.get('decimal_places', 2),
                    'theme': settings.get('theme', 'light'),
                    'auto_save': True,
                    'show_tooltips': True,
                    'compact_view': False
                }
                # Merge user-specific preferences if available
                try:
                    conn = db_manager.get_connection()
                    cur = conn.cursor()
                    cur.execute('SELECT preferences FROM user_preferences WHERE user_id = ?', (user_id,))
                    row = cur.fetchone()
                    if row and row['preferences']:
                        user_prefs = json.loads(row['preferences'])
                        if isinstance(user_prefs, dict):
                            preferences.update(user_prefs)
                except Exception as _e:
                    pass

                return jsonify({'success': True, 'preferences': preferences})
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la récupération des préférences: {str(e)}'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Cette fonctionnalité n\'est pas disponible en mode minimal'
            })
    
    @settings_bp.route('/api/settings/notifications', methods=['GET'])
    def get_notifications():
        """Get notification settings"""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'success': False, 'error': 'Utilisateur non authentifié'})
                
                # Get notification settings from database
                settings = db_manager.get_app_settings()
                
                # Default notification settings (app-level)
                notifications = {
                    'email_notifications': settings.get('email_notifications', True),
                    'low_stock_alerts': True,
                    'sales_reports': True,
                    'system_alerts': True,
                    'backup_notifications': settings.get('auto_backup', True),
                    'daily_summary': False,
                    'weekly_reports': False
                }
                # Merge per-user notification prefs if available
                try:
                    conn = db_manager.get_connection()
                    cur = conn.cursor()
                    cur.execute('SELECT preferences FROM notification_preferences WHERE user_id = ?', (user_id,))
                    row = cur.fetchone()
                    if row and row['preferences']:
                        user_notif = json.loads(row['preferences'])
                        if isinstance(user_notif, dict):
                            # If saved structure is nested (email/browser/sound), return as-is
                            # Frontend can handle nested when provided.
                            notifications = user_notif
                except Exception as _e:
                    pass

                return jsonify({'success': True, 'notifications': notifications})
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la récupération des notifications: {str(e)}'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Cette fonctionnalité n\'est pas disponible en mode minimal'
            })

    @settings_bp.route('/api/settings/update-security', methods=['POST'])
    def update_security():
        """Persist per-user security preferences (auto logout, login notifications, activity log)."""
        if MODULES_AVAILABLE and db_manager is not None:
            try:
                data = request.get_json() or {}
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'success': False, 'error': 'Utilisateur non authentifié'})

                conn = db_manager.get_connection()
                cursor = conn.cursor()

                # Ensure user_preferences exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'")
                if cursor.fetchone() is None:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_preferences (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            preferences TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    ''')
                    conn.commit()

                # Load existing preferences
                cursor.execute('SELECT preferences FROM user_preferences WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                existing = {}
                if row and row['preferences']:
                    try:
                        existing = json.loads(row['preferences'])
                    except Exception:
                        existing = {}

                # Merge security subset
                security = existing.get('security', {})
                for key in ('auto_logout', 'auto_logout_time', 'login_notifications', 'activity_log'):
                    if key in data:
                        security[key] = data[key]
                existing['security'] = security

                # Save back
                preferences_json = json.dumps(existing)
                cursor.execute('SELECT id FROM user_preferences WHERE user_id = ?', (user_id,))
                if cursor.fetchone():
                    cursor.execute('''
                        UPDATE user_preferences
                        SET preferences = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (preferences_json, user_id))
                else:
                    cursor.execute('''
                        INSERT INTO user_preferences (user_id, preferences)
                        VALUES (?, ?)
                    ''', (user_id, preferences_json))
                conn.commit()

                # Non-blocking log
                try:
                    db_manager.log_user_action(user_id, 'update_security', 'Mise à jour des préférences de sécurité')
                except Exception:
                    pass

                return jsonify({'success': True, 'message': 'Préférences de sécurité mises à jour'})
            except Exception as e:
                logger.error(f"Error updating security preferences: {e}")
                return jsonify({'success': False, 'error': str(e)})
        else:
            return jsonify({'success': False, 'error': 'Cette fonctionnalité n\'est pas disponible en mode minimal'})
    
    # Register the blueprint with the app
    app.register_blueprint(settings_bp)
