import asyncio
from playwright.async_api import async_playwright
import os

BASE = os.environ.get('APP_BASE', 'http://127.0.0.1:5000')

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        messages = []
        page.on('console', lambda msg: messages.append(('console', msg.type, msg.text)))
        async def _on_page_error(exc):
            try:
                stack = exc.stack if hasattr(exc, 'stack') else None
            except Exception:
                stack = None
            info = ('pageerror', getattr(exc, 'message', str(exc)), stack)
            messages.append(info)
            # Try to capture Chart internals at the moment of error
            try:
                snap = await page.evaluate('''() => {
                    const out = { instances: [] };
                    try {
                        const Chart = window.Chart;
                        out.ChartDefined = !!Chart;
                        if (Chart && Chart.instances) {
                            for (const k in Chart.instances) {
                                const inst = Chart.instances[k];
                                out.instances.push({ key:k, canvasId: inst && inst.canvas ? inst.canvas.id || null : null, canvasPresent: !!(inst && inst.canvas && document.contains(inst.canvas)) });
                            }
                        } else if (Chart && typeof Chart.getChart === 'function') {
                            Array.from(document.querySelectorAll('canvas')).forEach(c => {
                                try { const i = Chart.getChart(c); out.instances.push({ canvasId: c.id||null, hasInstance: !!i, instCanvasPresent: !!(i && i.canvas && document.contains(i.canvas)) }); } catch(e) { out.instances.push({ canvasId: c.id||null, err: String(e) }); }
                            });
                        }
                    } catch (e) { out.err = String(e); }
                    return out;
                ''')
            except Exception as e:
                snap = {'error': str(e)}
            messages.append(('chart-snapshot', snap))

        page.on('pageerror', lambda exc: asyncio.create_task(_on_page_error(exc)))
        await page.goto(f"{BASE}/autologin/inventory")
        await page.wait_for_load_state('networkidle')
        await page.goto(f"{BASE}/finance")
        await page.wait_for_timeout(3000)
        # Gather in-page diagnostics: canvases and chart globals
        try:
            diag = await page.evaluate('''() => {
                const canvases = Array.from(document.querySelectorAll('canvas')).map(c => ({ id: c.id || null, hasGetContext: !!(c.getContext && c.getContext('2d')) }));
                const globals = {};
                try { globals.salesChart = !!(window.salesChart); } catch (e) { globals.salesChart = 'err'; }
                try { globals.revenueChart = !!(window.__finance__ && window.__finance__.revenueChart); } catch (e) { globals.revenueChart = 'err'; }
                try { globals.ChartDefined = !!window.Chart; } catch (e) { globals.ChartDefined = 'err'; }
                // Inspect Chart instances associated with canvases
                const chartInfos = [];
                try {
                    const Chart = window.Chart;
                    if (Chart && typeof Chart.getChart === 'function') {
                        document.querySelectorAll('canvas').forEach(c => {
                            try {
                                const inst = Chart.getChart(c);
                                chartInfos.push({ canvasId: c.id || null, hasInstance: !!inst, instanceCanvasNull: inst ? (inst.canvas ? false : true) : null });
                            } catch (e) {
                                chartInfos.push({ canvasId: c.id || null, err: String(e) });
                            }
                        });
                    } else if (Chart && Chart.instances) {
                        try {
                            for (const k in Chart.instances) {
                                const inst = Chart.instances[k];
                                chartInfos.push({ key: k, canvasId: inst && inst.canvas ? (inst.canvas.id || null) : null, instanceCanvasNull: !(inst && inst.canvas) });
                            }
                        } catch (e) { chartInfos.push({ instancesError: String(e) }); }
                    }
                } catch (e) { chartInfos.push({ inspectError: String(e) }); }

                return { canvases, globals, chartInfos };
            }''')
        except Exception as e:
            diag = {'error': str(e)}

        for m in messages:
            print(m)
        print('\nDIAGNOSTICS:', diag)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
