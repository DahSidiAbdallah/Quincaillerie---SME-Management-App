import sqlite3
import os
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'data', 'quincaillerie.db')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
print('DB:', DB)
print('\nLast 50 sales:')
c.execute("SELECT id, sale_date, total_amount, is_deleted FROM sales ORDER BY sale_date DESC LIMIT 50")
for r in c.fetchall():
    print(r['id'], r['sale_date'], r['total_amount'], r['is_deleted'])

from datetime import timedelta
end = datetime.now().strftime('%Y-%m-%d')
print('\nSales since 4 weeks ago (%s):' % end)
c.execute("SELECT id, sale_date, total_amount, is_deleted FROM sales WHERE sale_date >= date(?, '-4 weeks') ORDER BY sale_date DESC", (end,))
rows = c.fetchall()
if not rows:
    print('No rows in 4-week window')
else:
    for r in rows:
        print(r['id'], r['sale_date'], r['total_amount'], r['is_deleted'])
conn.close()
