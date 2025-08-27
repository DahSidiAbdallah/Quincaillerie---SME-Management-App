import sqlite3
import os
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'data', 'quincaillerie.db')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
end = datetime.now().strftime('%Y-%m-%d')
print('Using end date:', end)
q = "SELECT strftime('%Y-%W', sale_date) as week, MIN(sale_date) as first_date, MAX(sale_date) as last_date, SUM(total_amount) as total FROM sales WHERE sale_date >= date(?, '-4 weeks') AND is_deleted = 0 GROUP BY week ORDER BY week"
print('Query:', q)
c.execute(q, (end,))
rows = c.fetchall()
if not rows:
    print('No rows returned for weekly aggregation')
else:
    for r in rows:
        print(r['week'], r['first_date'], r['last_date'], r['total'])
conn.close()
