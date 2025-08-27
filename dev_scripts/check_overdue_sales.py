#!/usr/bin/env python3
import sqlite3, os
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'data', 'quincaillerie.db'))
print('DB:', DB)
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
q = '''
SELECT id, invoice_number, is_credit, credit_due_date, status, total_amount, paid_amount
FROM sales
WHERE is_credit = 1 AND credit_due_date IS NOT NULL AND DATE(credit_due_date) < DATE('now')
ORDER BY DATE(credit_due_date) ASC
'''
c.execute(q)
rows = [dict(r) for r in c.fetchall()]
print('Found', len(rows), 'credit sales with credit_due_date < today:\n')
for r in rows:
    print(f"id={r['id']}, invoice={r['invoice_number']}, due={r['credit_due_date']}, status={r['status']}, total={r['total_amount']}, paid={r.get('paid_amount')}, remaining={r.get('remaining_amount')}")
conn.close()
