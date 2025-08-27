import sqlite3, os
DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'data', 'quincaillerie.db')
conn = sqlite3.connect(DB)
c = conn.cursor()
end = '2025-08-27'
print('date(?, "-4 weeks") =>', c.execute("SELECT date(?, '-4 weeks')", (end,)).fetchone())
print('Rows where sale_date >= that date:')
q = "SELECT id, sale_date, total_amount FROM sales WHERE sale_date >= date(?, '-4 weeks') ORDER BY sale_date DESC"
rows = c.execute(q, (end,)).fetchall()
print('Count:', len(rows))
for r in rows[:20]:
    print(r)
conn.close()
