from playwright.sync_api import sync_playwright
import json
BASE='http://127.0.0.1:5000'
msgs = []
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    def onconsole(msg):
        try:
            msgs.append({'type': msg.type, 'text': msg.text, 'location': msg.location})
        except Exception as e:
            msgs.append({'type': msg.type, 'text': msg.text})
    page.on('console', onconsole)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE + '/autologin/inventory')
    page.wait_for_load_state('networkidle')
    page.goto(BASE + '/finance')
    page.wait_for_selector('#revenueChart', timeout=10000)
    # wait longer for charts to attempt update
    page.wait_for_timeout(3000)
    # capture console snapshot
    print('CONSOLES:')
    print(json.dumps(msgs, indent=2, ensure_ascii=False))
    print('\nPAGE ERRORS:')
    print(json.dumps(errors, indent=2, ensure_ascii=False))
    page.screenshot(path='tests/e2e/screenshots/finance_console_debug.png', full_page=True)
    print('\nScreenshot saved to tests/e2e/screenshots/finance_console_debug.png')
    b.close()
