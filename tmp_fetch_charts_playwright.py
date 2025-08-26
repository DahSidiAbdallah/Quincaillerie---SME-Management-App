from playwright.sync_api import sync_playwright
import json
BASE='http://127.0.0.1:5000'
with sync_playwright() as p:
    b=p.chromium.launch()
    page=b.new_page()
    page.goto(BASE+'/autologin/inventory')
    page.wait_for_load_state('networkidle')
    data=page.evaluate("async () => { const r = await fetch('/api/finance/charts?period=month'); return r.json(); }")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    b.close()
