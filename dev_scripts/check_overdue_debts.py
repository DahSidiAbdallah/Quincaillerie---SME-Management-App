#!/usr/bin/env python3
import sqlite3, os
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'data', 'quincaillerie.db'))
print('DB:', DB)
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
q = '''
SELECT id, client_name, due_date, status, remaining_amount
FROM client_debts
WHERE due_date IS NOT NULL AND DATE(due_date) < DATE('now') AND remaining_amount > 0
ORDER BY DATE(due_date) ASC
'''
c.execute(q)
rows = [dict(r) for r in c.fetchall()]
print('Found', len(rows), 'overdue client_debts rows:\n')
for r in rows:
    print(f"id={r['id']}, client={r['client_name']}, due={r['due_date']}, status={r['status']}, remaining={r['remaining_amount']}")
conn.close()
