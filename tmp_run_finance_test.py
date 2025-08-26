import sqlite3
import app.app as app_module
from app.api import reports as reports_mod

# Setup test client and session like the pytest fixture
app = app_module.app
app.config['TESTING'] = True
with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = 1
    
    def fake_conn():
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('CREATE TABLE sales (id INTEGER, sale_date TEXT, total_amount REAL, is_deleted INTEGER)')
        cur.execute('''CREATE TABLE expenses (
            id INTEGER, expense_date TEXT, amount REAL, category TEXT, subcategory TEXT, is_deleted INTEGER
        )''')
        cur.execute("INSERT INTO sales VALUES (1, '2024-01-01', 100, 0)")
        cur.execute("INSERT INTO expenses VALUES (1, '2024-01-01', 50, 'business', 'Achats', 0)")
        conn.commit()
        return conn

    app_module.db_manager.get_connection = fake_conn
    resp = client.get('/api/finance/charts?period=week')
    print('status', resp.status_code)
    print(resp.get_data(as_text=True))
