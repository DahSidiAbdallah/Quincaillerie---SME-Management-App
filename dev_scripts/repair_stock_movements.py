import sqlite3

# This script will insert missing 'out' stock movements for all sale_items that do not have a corresponding stock_movement.

db = 'app/db/quincaillerie.db'
con = sqlite3.connect(db)
cur = con.cursor()

# Get all sale_items
cur.execute('SELECT id, product_id, sale_id, quantity, unit_price, total_price FROM sale_items')
sale_items = cur.fetchall()

# Get all existing 'out' stock_movements
cur.execute("SELECT product_id, quantity, unit_price, total_amount FROM stock_movements WHERE movement_type='out'")
existing_movements = set(cur.fetchall())

# Map sale_id to customer_name
cur.execute('SELECT id, customer_name FROM sales')
sale_customers = {row[0]: row[1] for row in cur.fetchall()}

inserted = []
for si in sale_items:
    _, product_id, sale_id, quantity, unit_price, total_price = si
    key = (product_id, quantity, unit_price, total_price)
    if key not in existing_movements:
        cur.execute('INSERT INTO stock_movements (product_id, movement_type, quantity, unit_price, total_amount, reference, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (product_id, 'out', quantity, unit_price, total_price, f'Vente #{sale_id}', f'Vente à {sale_customers.get(sale_id, "Client")}', 1))
        inserted.append((product_id, sale_id, quantity, unit_price, total_price))
con.commit()
print('Inserted missing stock movements:', inserted)
con.close()
