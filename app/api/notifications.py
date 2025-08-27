from flask import Blueprint, request, jsonify
from app.data.database import DatabaseManager

notifications_api = Blueprint('notifications_api', __name__)

db = DatabaseManager()

@notifications_api.route('/notifications', methods=['GET'])
def get_notifications():
    """
    Get notifications for the current user (or all, if not user-specific).
    Query params:
        unread (optional): if '1', only return unread notifications
        limit (optional): max number of notifications to return
    """
    # TODO: Replace with user-specific logic if needed
    unread = request.args.get('unread')
    limit = request.args.get('limit', type=int)
    notifications = db.get_notifications(unread_only=(unread == '1'), limit=limit)
    return jsonify({'notifications': notifications})

@notifications_api.route('/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    db.mark_notification_read(notification_id)
    return jsonify({'success': True})
