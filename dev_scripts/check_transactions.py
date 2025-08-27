#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'app', 'data', 'quincaillerie.db')
DB_PATH = os.path.abspath(DB_PATH)

query = '''
    SELECT s.id as sale_id, DATE(s.sale_date) AS date, s.created_at, s.total_amount AS amount,
           'Vente' AS description, 'income' AS type, 'ventes' AS category, '' AS subcategory, s.status AS payment_status
    FROM sales s
    ORDER BY date DESC, created_at DESC
'''

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute(query)
rows = [dict(r) for r in cur.fetchall()]
print(f"DB: {DB_PATH}")
print(f"Found {len(rows)} sale transactions:\n")
for r in rows:
    print(f"sale_id={r.get('sale_id')}, date={r.get('date')}, amount={r.get('amount')}, status={r.get('payment_status')}")

conn.close()
