#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'app', 'data', 'quincaillerie.db')
DB_PATH = os.path.abspath(DB_PATH)

query = '''
    SELECT id, date, created_at, amount, description, type, category, subcategory, payment_status
    FROM (
        SELECT id, DATE(entry_date) AS date, created_at, amount, source AS description,
               'income' AS type, 'capital' AS category, 'capital' AS subcategory, '' AS payment_status
        FROM capital_entries
        UNION ALL
        SELECT id, DATE(expense_date) AS date, created_at, amount, description,
               'expense' AS type, category, COALESCE(subcategory, '') AS subcategory, '' AS payment_status
        FROM expenses
        UNION ALL
        SELECT s.id, DATE(s.sale_date) AS date, s.created_at, s.total_amount AS amount,
               'Vente' AS description, 'income' AS type, 'ventes' AS category, '' AS subcategory, s.status AS payment_status
        FROM sales s
    )
    ORDER BY date DESC, created_at DESC
'''

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute(query)
rows = [dict(r) for r in cur.fetchall()]
print(f"DB: {DB_PATH}")
print(f"Found {len(rows)} transactions (union):\n")
for r in rows:
    print(f"id={r.get('id')}, date={r.get('date')}, amount={r.get('amount')}, status={r.get('payment_status')}, type={r.get('type')}")

conn.close()
