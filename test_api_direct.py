import sqlite3
db = sqlite3.connect('app/data/quincaillerie.db')
# Set all credit sales to 'pending' first
db.execute("UPDATE sales SET status='pending' WHERE is_credit=1")
db.commit()
# Now set overdue
db.execute("UPDATE sales SET credit_due_date='2025-08-01', status='retard' WHERE is_credit=1 AND status='pending'")
db.commit()
db.close()