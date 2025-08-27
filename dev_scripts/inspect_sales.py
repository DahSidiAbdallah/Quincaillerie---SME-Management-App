import sqlite3, json, datetime
from pathlib import Path
p = Path(r"c:/Users/DAH/Downloads/Quincaillerie & SME Management App/app/data/quincaillerie.db")
conn = sqlite3.connect(str(p))
conn.row_factory = sqlite3.Row
cur = conn.cursor()
# Sales with credit_due_date
cur.execute("SELECT id, status, is_credit, credit_due_date, paid_amount, total_amount FROM sales WHERE credit_due_date IS NOT NULL ORDER BY id DESC LIMIT 50")
rows = [dict(r) for r in cur.fetchall()]
# Overdue according to DB date comparison
today = datetime.date.today().isoformat()
cur.execute("SELECT id, status, is_credit, credit_due_date, paid_amount, total_amount FROM sales WHERE is_credit=1 AND status='pending' AND credit_due_date IS NOT NULL AND credit_due_date < ? ORDER BY id DESC", (today,))
overdue_pending = [dict(r) for r in cur.fetchall()]
# Any with status='retard'
cur.execute("SELECT id, status, is_credit, credit_due_date, paid_amount, total_amount FROM sales WHERE status='retard' ORDER BY id DESC LIMIT 50")
retard = [dict(r) for r in cur.fetchall()]
print(json.dumps({'today': today, 'all_credit_sales_count': len(rows), 'sample': rows[:10], 'overdue_pending': overdue_pending, 'retard': retard}, default=str, ensure_ascii=False, indent=2))
conn.close()
