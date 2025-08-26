// reports-charts.js
// Responsible for initializing and updating charts on the reports page.
(function(){
    function ensureChartJs() {
        if (window.Chart) return Promise.resolve();
        return new Promise(resolve => {
            const s = document.createElement('script');
            s.src = '/static/js/chart.umd.min.js';
            s.onload = () => resolve();
            s.onerror = () => { console.warn('Failed to load local Chart.js UMD'); resolve(); };
            try { if (document.head) document.head.appendChild(s); else document.documentElement.appendChild(s); } catch (e) { try { document.documentElement.appendChild(s); } catch (e2) { resolve(); } }
        });
    }

    // wait for an element to appear in the DOM (defensive for race conditions)
    function waitForEl(id, maxAttempts = 40, delay = 50) {
        return new Promise(resolve => {
            let attempts = 0;
            const tick = () => {
                const el = document.getElementById(id);
                if (el) return resolve(el);
                attempts++;
                if (attempts >= maxAttempts) return resolve(null);
                setTimeout(tick, delay);
            };
            tick();
        });
    }

    async function init(manager) {
        await ensureChartJs();
        // create or refresh charts (defensive: wait for canvases and chart lib)
        try {
            if (!window.Chart) {
                console.warn('Chart.js not available after injection');
                return;
            }

            // sales
            const sEl = await waitForEl('salesChart');
            if (sEl) {
                if (manager.salesChart && typeof manager.salesChart.destroy === 'function') manager.salesChart.destroy();
                const ctx = sEl.getContext && sEl.getContext('2d');
                if (ctx) manager.salesChart = new Chart(ctx, { type:'line', data:{ labels:[], datasets:[{ label:`Ventes (${window.AppConfig?.currentCurrency||'MRU'})`, data:[], borderColor:'rgb(59,130,246)', backgroundColor:'rgba(59,130,246,0.1)', fill:true, tension:0.4 }] }, options:{ responsive:true, maintainAspectRatio:false } });
            }

            const prodEl = await waitForEl('productPerformanceChart');
            if (prodEl) {
                if (manager.productChart && typeof manager.productChart.destroy === 'function') manager.productChart.destroy();
                const ctx = prodEl.getContext && prodEl.getContext('2d');
                if (ctx) manager.productChart = new Chart(ctx, { type:'bar', data:{ labels:[], datasets:[{ label:'Quantité vendue', data:[], backgroundColor:'rgba(99,102,241,0.8)'}] }, options:{ responsive:true, maintainAspectRatio:false } });
            }

            const catEl = await waitForEl('categoryDistributionChart');
            if (catEl) {
                if (manager.categoryChart && typeof manager.categoryChart.destroy === 'function') manager.categoryChart.destroy();
                const ctx = catEl.getContext && catEl.getContext('2d');
                if (ctx) manager.categoryChart = new Chart(ctx, { type:'doughnut', data:{ labels:[], datasets:[{ data:[], backgroundColor:['#60A5FA','#34D399','#FBBF24','#F87171','#A78BFA'] }] }, options:{ responsive:true, maintainAspectRatio:false } });
            }

            const pfEl = await waitForEl('profitOverTimeChart');
            if (pfEl) {
                if (manager.profitChart && typeof manager.profitChart.destroy === 'function') manager.profitChart.destroy();
                const ctx = pfEl.getContext && pfEl.getContext('2d');
                if (ctx) manager.profitChart = new Chart(ctx, { type:'line', data:{ labels:[], datasets:[{ label:'Profit', data:[], borderColor:'#10B981', backgroundColor:'rgba(16,185,129,0.08)', fill:true }] }, options:{ responsive:true, maintainAspectRatio:false } });
            }

            const clEl = await waitForEl('customerLTVChart');
            if (clEl) {
                if (manager.customerChart && typeof manager.customerChart.destroy === 'function') manager.customerChart.destroy();
                const ctx = clEl.getContext && clEl.getContext('2d');
                if (ctx) manager.customerChart = new Chart(ctx, { type:'bar', data:{ labels:[], datasets:[{ label:'LTV', data:[], backgroundColor:'#F59E0B' }] }, options:{ responsive:true, maintainAspectRatio:false } });
            }

        } catch (e) {
            console.error('reports-charts init error', e);
        }

        // immediately fetch and populate data according to manager filters
        await updateAll(manager);
    }

    async function updateAll(manager) {
        if (!manager) return;
        const dr = (typeof manager.getDateRangeParams === 'function') ? manager.getDateRangeParams() : { startDate:'', endDate:'' };
        try {
            // dashboard analytics
            const q = `?start_date=${encodeURIComponent(dr.startDate)}&end_date=${encodeURIComponent(dr.endDate)}`;
            const da = await apiFetch(`/api/reports/dashboard-analytics${q}`).catch(()=>null);
            if (da?.analytics) {
                const prod = da.analytics.product_performance || [];
                const cat = da.analytics.category_distribution || [];
                if (manager.productChart) { manager.productChart.data.labels = prod.map(p=>p.name); manager.productChart.data.datasets[0].data = prod.map(p=>p.quantity_sold||p.quantity||0); manager.productChart.update(); }
                if (manager.categoryChart) { manager.categoryChart.data.labels = cat.map(c=>c.category); manager.categoryChart.data.datasets[0].data = cat.map(c=>c.revenue||0); manager.categoryChart.update(); }
                if (manager.salesChart && Array.isArray(da.analytics.sales_trend)) { manager.salesChart.data.labels = da.analytics.sales_trend.map(s=>s.date); manager.salesChart.data.datasets[0].data = da.analytics.sales_trend.map(s=>s.revenue); manager.salesChart.update(); }
            }

            // profit analysis
            const pa = await apiFetch(`/api/reports/profit-analysis${q}`).catch(()=>null);
            if (pa?.profit_by_period && manager.profitChart) {
                const labels = pa.profit_by_period.map(p=>p.period);
                const profits = pa.profit_by_period.map(p=>p.profit || 0);
                manager.profitChart.data.labels = labels; manager.profitChart.data.datasets[0].data = profits; manager.profitChart.update();
            }

            // customer analysis
            const ca = await apiFetch(`/api/reports/customer-analysis${q}`).catch(()=>null);
            if (ca?.customers && manager.customerChart) {
                const top = (ca.customers || []).slice(0,10);
                manager.customerChart.data.labels = top.map(c=>c.name||c.id);
                manager.customerChart.data.datasets[0].data = top.map(c=>c.lifetime_value || c.orders_count || 0);
                manager.customerChart.update();
            }
        } catch (e) {
            console.error('reports-charts updateAll error', e);
        }
    }

    // expose
    window.ReportsCharts = { init, updateAll };
})();
