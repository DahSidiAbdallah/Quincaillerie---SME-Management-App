import sys, os, sqlite3
sys.path.insert(0, r'C:\Users\DAH\Downloads\Quincaillerie & SME Management App')
from app.app import app
import app.api.reports as reports

# create test client
app.config['TESTING'] = True
with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = 1
    # monkeypatch-like: replace get_connection
    def fake_conn():
        conn = sqlite3.connect(':memory:')
        cur = conn.cursor()
        cur.execute('CREATE TABLE sales (id INTEGER, sale_date TEXT, customer_name TEXT, total_amount REAL, paid_amount REAL, payment_method TEXT, is_credit INTEGER, created_by INTEGER)')
        cur.execute('CREATE TABLE users (id INTEGER, username TEXT)')
        conn.commit()
        return conn
    reports.db_manager.get_connection = fake_conn
    reports.db_manager.log_user_action = lambda *a, **k: None
    resp = client.get('/api/reports/export/sales?start_date=2024-01-01&end_date=2024-01-31')
    print('export status', resp.status_code, resp.content_type)
    # test dashboard analytics
    def fake_conn2():
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('CREATE TABLE sales (id INTEGER, sale_date TEXT, total_amount REAL, is_deleted INTEGER)')
        cur.execute('CREATE TABLE sale_items (id INTEGER, sale_id INTEGER, product_id INTEGER, quantity INTEGER, total_price REAL, profit_margin REAL)')
        cur.execute('CREATE TABLE products (id INTEGER, name TEXT, category TEXT)')
        cur.execute("INSERT INTO products VALUES (1,'P1','CatA')")
        cur.execute("INSERT INTO sales VALUES (1,'2025-08-01',100,0)")
        cur.execute("INSERT INTO sale_items VALUES (1,1,1,2,200,50)")
        conn.commit()
        return conn
    reports.db_manager.get_connection = fake_conn2
    resp2 = client.get('/api/reports/dashboard-analytics')
    print('analytics status', resp2.status_code, resp2.get_json())
