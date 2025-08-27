#!/usr/bin/env python3
import sqlite3
DB='app/data/quincaillerie.db'
conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
c=conn.cursor()
c.execute('SELECT count(*) as cnt FROM user_activity_log')
print('count:', c.fetchone()['cnt'])
c.execute('SELECT id, user_id, action_type, description, table_affected, record_id, meta, action_time, created_at FROM user_activity_log ORDER BY id DESC LIMIT 10')
for r in c.fetchall():
    print(dict(r))
conn.close()
