#!/usr/bin/env python3
"""Small smoke test: find a recent activity and call the matches endpoint."""
import sqlite3
import json
import urllib.request
import urllib.parse
import sys

DB = 'app/data/quincaillerie.db'
BASE = 'http://127.0.0.1:5000'

def find_activity_id():
    try:
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, description FROM user_activity_log WHERE lower(description) LIKE '%vente%' OR lower(description) LIKE '%vente cr%' LIMIT 1")
        row = cur.fetchone()
        if row:
            return row['id'], row['description']
        cur.execute('SELECT id, description FROM user_activity_log LIMIT 1')
        row = cur.fetchone()
        if row:
            return row['id'], row['description']
    except Exception as e:
        print('DB error:', e)
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return None, None

def call_matches(aid):
    url = f"{BASE}/api/dashboard/activities/matches?id={urllib.parse.quote(str(aid))}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            text = resp.read().decode('utf-8')
            try:
                data = json.loads(text)
                print(json.dumps(data, ensure_ascii=False, indent=2))
            except Exception:
                print('Non-JSON response:', text)
    except Exception as e:
        print('HTTP error:', e)

if __name__ == '__main__':
    aid, desc = find_activity_id()
    if not aid:
        print('No activity id found to test')
        sys.exit(2)
    print('Testing activity id:', aid)
    print('Description:', desc)
    call_matches(aid)
