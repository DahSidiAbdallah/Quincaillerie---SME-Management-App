import sqlite3, os, json
from pathlib import Path
candidates = [
    Path(r"c:/Users/DAH/Downloads/Quincaillerie & SME Management App/app/quincaillerie.db"),
    Path(r"c:/Users/DAH/Downloads/Quincaillerie & SME Management App/app/data/quincaillerie.db"),
    Path(r"c:/Users/DAH/Downloads/Quincaillerie & SME Management App/app/db/quincaillerie.db"),
    Path(r"c:/Users/DAH/Downloads/Quincaillerie & SME Management App/db/quincaillerie.db"),
]
out = []
for p in candidates:
    item = {"path": str(p), "exists": p.exists(), "tables": None, "error": None}
    if p.exists():
        try:
            conn = sqlite3.connect(str(p))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            item['tables'] = [r[0] for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            item['error'] = str(e)
    out.append(item)
print(json.dumps(out, ensure_ascii=False, indent=2))
