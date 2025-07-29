#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Admin API blueprint for system settings and backups"""

from flask import Blueprint, request, jsonify, session, send_file
import os
import json
import logging
from datetime import datetime

from db.database import DatabaseManager
from offline.sync_manager import SyncManager

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

db_manager = DatabaseManager()
sync_manager = SyncManager()

BACKUP_DIR = os.path.join('backups')
os.makedirs(BACKUP_DIR, exist_ok=True)


def require_admin():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès administrateur requis'}), 403
    return None


@admin_bp.route('/settings', methods=['GET', 'POST'])
def app_settings():
    auth_check = require_admin()
    if auth_check:
        return auth_check

    if request.method == 'GET':
        settings = db_manager.get_app_settings()
        return jsonify({'success': True, 'settings': settings})

    data = request.get_json() or {}
    db_manager.set_app_settings(data)
    db_manager.log_user_action(session['user_id'], 'update_settings', 'Mise à jour des paramètres')
    return jsonify({'success': True})


@admin_bp.route('/backups', methods=['GET', 'POST'])
def backups_list_create():
    auth_check = require_admin()
    if auth_check:
        return auth_check

    if request.method == 'POST':
        export = sync_manager.export_offline_data()
        if not export.get('success'):
            return jsonify({'success': False, 'message': export.get('error', 'Erreur export')}), 500
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(BACKUP_DIR, f'backup_{timestamp}.json')
        with open(path, 'w') as f:
            json.dump(export['data'], f, ensure_ascii=False, indent=2)
        db_manager.log_user_action(session['user_id'], 'create_backup', f'Backup {path}')
        return jsonify({'success': True})

    backups = []
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
    return jsonify({'success': True, 'backups': backups})


@admin_bp.route('/backups/<backup_id>', methods=['GET', 'DELETE'])
def backup_download_delete(backup_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check

    path = os.path.join(BACKUP_DIR, backup_id)
    if not os.path.exists(path):
        return jsonify({'success': False, 'message': 'Fichier introuvable'}), 404

    if request.method == 'DELETE':
        os.remove(path)
        db_manager.log_user_action(session['user_id'], 'delete_backup', backup_id)
        return jsonify({'success': True})

    return send_file(path, as_attachment=True)

