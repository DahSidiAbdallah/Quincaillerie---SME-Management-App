#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safe one-off migration: add structured columns to user_activity_log and backfill from descriptions.
Creates a timestamped backup of the sqlite DB before making changes.
Run from project root: python dev_scripts/enrich_activity_log.py
"""
import os
import sys
import shutil
import json
import re
from datetime import datetime

# Ensure project root is on sys.path so app/data can be imported reliably
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import DatabaseManager from the app package (or fallback)
try:
    from app.data.database import DatabaseManager
except Exception:
    try:
        from db.database import DatabaseManager  # type: ignore
    except Exception:
        # As a final fallback, try importing directly from expected file path
        sys.path.insert(0, os.path.join(PROJECT_ROOT, 'app', 'data'))
        from database import DatabaseManager  # type: ignore

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Instantiate manager to get db path
dbm = DatabaseManager()
db_path = dbm.db_path

print(f"Database path: {db_path}")

# Make backup
backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
print(f"Creating backup: {backup_path}")
shutil.copy2(db_path, backup_path)
print("Backup created.")

conn = dbm.get_connection()
cursor = conn.cursor()

# Ensure columns exist: table_affected TEXT, record_id INTEGER, meta TEXT
cursor.execute("PRAGMA table_info(user_activity_log)")
cols = [c[1] for c in cursor.fetchall()]

added = []
if 'table_affected' not in cols:
    try:
        cursor.execute("ALTER TABLE user_activity_log ADD COLUMN table_affected TEXT")
        added.append('table_affected')
    except Exception as e:
        print(f"Failed to add table_affected: {e}")
if 'record_id' not in cols:
    try:
        cursor.execute("ALTER TABLE user_activity_log ADD COLUMN record_id INTEGER")
        added.append('record_id')
    except Exception as e:
        print(f"Failed to add record_id: {e}")
if 'meta' not in cols:
    try:
        cursor.execute("ALTER TABLE user_activity_log ADD COLUMN meta TEXT")
        added.append('meta')
    except Exception as e:
        print(f"Failed to add meta: {e}")

if added:
    conn.commit()
    print(f"Added columns: {', '.join(added)}")
else:
    print("Columns already present or none added.")

# Patterns to extract sale IDs
# Mapping of regex -> (table_affected, group index to extract id)
pattern_map = [
    # Sales references (various forms)
    (re.compile(r"vente\s+cr[eé]e(?:e)?\s+#?(\d+)", re.IGNORECASE), ('sales', 1)),
    (re.compile(r"suppression\s+vente\s+#?(\d+)", re.IGNORECASE), ('sales', 1)),
    (re.compile(r"annulation\s+vente\s+#?(\d+)", re.IGNORECASE), ('sales', 1)),
    (re.compile(r"#(\d+)\b", re.IGNORECASE), ('sales', 1)),  # generic #123 fallback

    # Stock or movement references (may include sale refs)
    (re.compile(r"Annulation vente #?(\d+)", re.IGNORECASE), ('sales', 1)),
    (re.compile(r"Ve?nte\s+#?(\d+)", re.IGNORECASE), ('sales', 1)),

    # User references (creation/deletion)
    (re.compile(r"utilisateur\s+#?(\d+)", re.IGNORECASE), ('users', 1)),
    (re.compile(r"utilisateur\s+ID\s+(\d+)", re.IGNORECASE), ('users', 1)),

    # Backups (store path or id as record_id may not be numeric; use meta)
    (re.compile(r"Backup\s+(.*)", re.IGNORECASE), ('backups', None)),
    (re.compile(r"backup\s+([A-Za-z0-9_\-\.]+)", re.IGNORECASE), ('backups', None)),

    # Payments/debts: try to capture sale_id or debt id if present
    (re.compile(r"vente\s+#?(\d+)\b", re.IGNORECASE), ('sales', 1)),
    (re.compile(r"dette\s+#?(\d+)\b", re.IGNORECASE), ('client_debts', 1)),
    (re.compile(r"paiement\s+dette[:\s]*#?(\d+)\b", re.IGNORECASE), ('client_debts', 1)),
]

# Select rows for processing
cursor.execute("SELECT id, user_id, action_type, description, table_affected, record_id, meta FROM user_activity_log")
rows = cursor.fetchall()

scanned = 0
matched = 0
updated = 0

for r in rows:
    scanned += 1
    rid = r['id'] if isinstance(r, dict) or hasattr(r, 'keys') else r[0]
    row = dict(r)
    # If already has both structured info, skip
    if row.get('table_affected') and row.get('record_id'):
        continue
    desc = (row.get('description') or '')
    matched_entry = None
    matched_value = None

    # Try each pattern in order
    for pat, (tbl, grp) in pattern_map:
        m = pat.search(desc)
        if not m:
            continue
        if grp is None:
            # Non-numeric id, store original capture in meta and set table_affected
            matched_entry = tbl
            matched_value = None
            capture = m.group(1) if m.groups() else None
            meta = {'original_description': desc, 'matched_pattern': pat.pattern, 'capture': capture}
            break
        else:
            try:
                val = int(m.group(grp))
                matched_entry = tbl
                matched_value = val
                meta = {'original_description': desc, 'matched_pattern': pat.pattern}
                break
            except Exception:
                # skip if group isn't numeric
                continue

    if matched_entry:
        matched += 1
        try:
            cursor.execute(
                "UPDATE user_activity_log SET table_affected = ?, record_id = ?, meta = ? WHERE id = ?",
                (matched_entry, matched_value, json.dumps(meta, ensure_ascii=False), rid)
            )
            updated += 1
        except Exception as e:
            print(f"Failed to update row {rid}: {e}")

conn.commit()
conn.close()

print(f"Scanned rows: {scanned}")
print(f"Matched rows: {matched}")
print(f"Updated rows: {updated}")
print("Migration complete. Keep the backup file safe before making further changes.")
