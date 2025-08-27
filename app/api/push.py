# API endpoint to trigger a test push notification (admin only)
from flask import Blueprint, request, jsonify, session
from flask import current_app as app

push_api = Blueprint('push_api', __name__)

# API endpoint to trigger a test push notification (admin only)
@push_api.route('/push/test', methods=['POST'])
def send_test_push():
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin only'}), 403
    send_push_to_all("Test Notification", "Ceci est une notification test !", "/dashboard")
    return jsonify({'success': True})

# In-memory store for demo; replace with persistent storage in production
PUSH_SUBSCRIPTIONS = []

@push_api.route('/push/subscribe', methods=['POST'])
def subscribe():
    sub = request.get_json()
    # Optionally associate with user_id from session
    user_id = session.get('user_id')
    sub['user_id'] = user_id
    # Prevent duplicates
    for s in PUSH_SUBSCRIPTIONS:
        if s.get('endpoint') == sub.get('endpoint'):
            return jsonify({'success': True})
    PUSH_SUBSCRIPTIONS.append(sub)
    app.logger.info(f"Push subscription added: {sub.get('endpoint')}")
    return jsonify({'success': True})

# Utility to send a push notification to all subscribers (for demo)
def send_push_to_all(title, body, url=None):
    import requests, json
    from pywebpush import webpush, WebPushException
    vapid_private_key = app.config.get('VAPID_PRIVATE_KEY')
    vapid_claims = {"sub": "mailto:admin@example.com"}
    for sub in PUSH_SUBSCRIPTIONS:
        try:
            webpush(
                subscription_info=sub,
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
        except WebPushException as ex:
            app.logger.error(f"WebPush failed: {ex}")
