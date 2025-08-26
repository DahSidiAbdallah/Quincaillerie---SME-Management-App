import asyncio
from playwright.async_api import async_playwright
import os

BASE = os.environ.get('APP_BASE', 'http://127.0.0.1:5000')

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Use autologin endpoint to set session then go to finance page
        await page.goto(f"{BASE}/autologin/inventory")
        await page.wait_for_load_state('networkidle')
        await page.goto(f"{BASE}/finance")
        # Wait for canvases to be available
        await page.wait_for_selector('#revenueChart', timeout=10000)
        await page.wait_for_selector('#expenseChart', timeout=10000)
        # Give charts time to load data and render
        await page.wait_for_timeout(2000)
        # Take screenshot
        os.makedirs('tests/e2e/screenshots', exist_ok=True)
        await page.screenshot(path='tests/e2e/screenshots/finance_charts.png', full_page=True)
        print('Screenshot saved to tests/e2e/screenshots/finance_charts.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
