import os
import sys
import sqlite3
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app
from app.api import ai_insights, reports


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        yield client


def test_sales_forecast_has_standard_fields(monkeypatch, client):
    """sales-forecast endpoint should provide forecastDays and summary"""
    monkeypatch.setattr(
        ai_insights.sales_forecaster,
        'predict_overall_sales',
        lambda days_ahead: {
            'forecast': [],
            'trend': 'stable',
            'total_predicted_revenue': 1000,
            'avg_daily_revenue': 100,
            'confidence': 0.8,
            'data_points': 1,
        }
    )
    resp = client.get('/api/ai/sales-forecast')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['forecast']['forecastDays'] == 7
    assert 'summary' in data['forecast']


def test_reports_export_sales_accepts_filters(monkeypatch, client):
    """export endpoint should accept date filters and return CSV"""
    def fake_conn():
        conn = sqlite3.connect(':memory:')
        cur = conn.cursor()
        cur.execute('CREATE TABLE sales (id INTEGER, sale_date TEXT, customer_name TEXT, total_amount REAL, paid_amount REAL, payment_method TEXT, is_credit INTEGER, created_by INTEGER)')
        cur.execute('CREATE TABLE users (id INTEGER, username TEXT)')
        conn.commit()
        return conn
    monkeypatch.setattr(reports.db_manager, 'get_connection', fake_conn)
    monkeypatch.setattr(reports.db_manager, 'log_user_action', lambda *a, **k: None)
    resp = client.get('/api/reports/export/sales?start_date=2024-01-01&end_date=2024-01-31')
    assert resp.status_code == 200
    assert 'text/csv' in resp.headers.get('Content-Type', '')
