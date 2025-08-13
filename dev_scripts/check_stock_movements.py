import sqlite3
import sys

# Usage: python check_stock_movements.py <db_path> <product_id>

def main():
    if len(sys.argv) != 3:
        print("Usage: python check_stock_movements.py <db_path> <product_id>")
        sys.exit(1)
    db_path = sys.argv[1]
    product_id = sys.argv[2]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check which date column exists
    cur.execute("PRAGMA table_info(stock_movements)")
    columns = [row[1] for row in cur.fetchall()]
    if 'movement_date' in columns:
        date_col = 'movement_date'
    elif 'created_at' in columns:
        date_col = 'created_at'
    else:
        date_col = 'id'  # fallback

    print(f"Stock movements for product_id={product_id} (type='out'):")
    cur.execute(f'''
        SELECT id, movement_type, quantity, unit_price, total_amount, reference, notes, {date_col}
        FROM stock_movements
        WHERE product_id = ? AND movement_type = 'out'
        ORDER BY {date_col} DESC
    ''', (product_id,))
    rows = cur.fetchall()
    for row in rows:
        print(dict(row))
    print(f"Total 'out' movements found: {len(rows)}")

if __name__ == "__main__":
    main()
