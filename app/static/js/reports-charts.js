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
                if (manager.salesChart && typeof manager.salesChart.destroy === 'function') try { manager.salesChart.destroy(); } catch(e){}
                // create with canvas element (avoid passing 2d context to keep Chart internals linked to element)
                try { manager.salesChart = new Chart(sEl, { type:'line', data:{ labels:[], datasets:[{ label:`Ventes (${window.AppConfig?.currentCurrency||'MRU'})`, data:[], borderColor:'rgb(59,130,246)', backgroundColor:'rgba(59,130,246,0.1)', fill:true, tension:0.4 }] }, options:{ animation: false, responsive:true, maintainAspectRatio:false } }); } catch(e){ console.error('salesChart create failed', e); }
            }

            const prodEl = await waitForEl('productPerformanceChart');
            if (prodEl) {
                if (manager.productChart && typeof manager.productChart.destroy === 'function') try { manager.productChart.destroy(); } catch(e){}
                try { manager.productChart = new Chart(prodEl, { type:'bar', data:{ labels:[], datasets:[{ label:'Quantité vendue', data:[], backgroundColor:'rgba(99,102,241,0.8)'}] }, options:{ animation:false, responsive:true, maintainAspectRatio:false } }); } catch(e){ console.error('productChart create failed', e); }
            }

            const catEl = await waitForEl('categoryDistributionChart');
            if (catEl) {
                if (manager.categoryChart && typeof manager.categoryChart.destroy === 'function') try { manager.categoryChart.destroy(); } catch(e){}
                try { manager.categoryChart = new Chart(catEl, { type:'doughnut', data:{ labels:[], datasets:[{ data:[], backgroundColor:['#60A5FA','#34D399','#FBBF24','#F87171','#A78BFA'] }] }, options:{ animation:false, responsive:true, maintainAspectRatio:false } }); } catch(e){ console.error('categoryChart create failed', e); }
            }

            const pfEl = await waitForEl('profitOverTimeChart');
            if (pfEl) {
                if (manager.profitChart && typeof manager.profitChart.destroy === 'function') try { manager.profitChart.destroy(); } catch(e){}
                try { manager.profitChart = new Chart(pfEl, { type:'line', data:{ labels:[], datasets:[{ label:'Profit', data:[], borderColor:'#10B981', backgroundColor:'rgba(16,185,129,0.08)', fill:true }] }, options:{ animation:false, responsive:true, maintainAspectRatio:false } }); } catch(e){ console.error('profitChart create failed', e); }
            }

            const clEl = await waitForEl('customerLTVChart');
            if (clEl) {
                if (manager.customerChart && typeof manager.customerChart.destroy === 'function') try { manager.customerChart.destroy(); } catch(e){}
                try { manager.customerChart = new Chart(clEl, { type:'bar', data:{ labels:[], datasets:[{ label:'LTV', data:[], backgroundColor:'#F59E0B' }] }, options:{ animation:false, responsive:true, maintainAspectRatio:false } }); } catch(e){ console.error('customerChart create failed', e); }
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
        const q = `?start_date=${encodeURIComponent(dr.startDate)}&end_date=${encodeURIComponent(dr.endDate)}`;

        // helper: try safe in-place update, return true on success
        const safeUpdate = (chart, applyDataFn) => {
            if (!chart) return false;
            try {
                applyDataFn(chart);
                if (typeof chart.update === 'function') chart.update();
                return true;
            } catch (err) {
                console.warn('safeUpdate failed', err);
                return false;
            }
        };

        // helper: replace canvas with fresh element and create chart instance
        const recreateOnCanvas = async (canvasId, createChartFn) => {
            const oldEl = document.getElementById(canvasId);
            if (!oldEl) return null;
            const newEl = document.createElement('canvas');
            if (oldEl.id) newEl.id = oldEl.id;
            if (oldEl.className) newEl.className = oldEl.className;
            if (oldEl.style && oldEl.style.cssText) newEl.style.cssText = oldEl.style.cssText;
            if (oldEl.getAttribute && oldEl.getAttribute('width')) newEl.setAttribute('width', oldEl.getAttribute('width'));
            if (oldEl.getAttribute && oldEl.getAttribute('height')) newEl.setAttribute('height', oldEl.getAttribute('height'));
            try { oldEl.parentNode.replaceChild(newEl, oldEl); } catch(e){ console.warn('canvas replace failed for', canvasId, e); }
            // allow scheduled tasks to settle
            await new Promise(r => setTimeout(r, 120));
            try { return createChartFn(newEl); } catch(e) { console.error('createChartFn failed for', canvasId, e); return null; }
        };

        try {
            // dashboard analytics
            const da = await apiFetch(`/api/reports/dashboard-analytics${q}`).catch(()=>null);
            if (da?.analytics) {
                const prod = da.analytics.product_performance || [];
                const cat = da.analytics.category_distribution || [];

                // productChart
                if (manager.productChart) {
                    const ok = safeUpdate(manager.productChart, ch => { ch.data.labels = prod.map(p=>p.name); ch.data.datasets[0].data = prod.map(p=>p.quantity_sold||p.quantity||0); });
                    if (!ok) {
                        // recreate
                        manager.productChart = await recreateOnCanvas('productPerformanceChart', (c)=> new Chart(c, { type:'bar', data:{ labels: prod.map(p=>p.name), datasets:[{ label:'Quantité vendue', data: prod.map(p=>p.quantity_sold||p.quantity||0), backgroundColor:'rgba(99,102,241,0.8)'}] }, options:{ animation:false, responsive:true, maintainAspectRatio:false } }));
                    }
                }

                // categoryChart
                if (manager.categoryChart) {
                    const ok = safeUpdate(manager.categoryChart, ch => { ch.data.labels = cat.map(c=>c.category); ch.data.datasets[0].data = cat.map(c=>c.revenue||0); });
                    if (!ok) {
                        manager.categoryChart = await recreateOnCanvas('categoryDistributionChart', (c)=> new Chart(c, { type:'doughnut', data:{ labels: cat.map(c=>c.category), datasets:[{ data: cat.map(c=>c.revenue||0), backgroundColor:['#60A5FA','#34D399','#FBBF24','#F87171','#A78BFA'] }] }, options:{ animation:false, responsive:true, maintainAspectRatio:false } }));
                    }
                }

                // salesChart
                if (manager.salesChart && Array.isArray(da.analytics.sales_trend)) {
                    const labels = da.analytics.sales_trend.map(s=>s.date);
                    const values = da.analytics.sales_trend.map(s=>s.revenue);
                    const ok = safeUpdate(manager.salesChart, ch => { ch.data.labels = labels; ch.data.datasets[0].data = values; });
                    if (!ok) {
                        manager.salesChart = await recreateOnCanvas('salesChart', (c)=> new Chart(c, { type:'line', data:{ labels: labels, datasets:[{ label:`Ventes (${window.AppConfig?.currentCurrency||'MRU'})`, data: values, borderColor:'rgb(59,130,246)', backgroundColor:'rgba(59,130,246,0.1)', fill:true, tension:0.4 }] }, options:{ animation:false, responsive:true, maintainAspectRatio:false } }));
                    }
                }
            }

            // profit analysis
            const pa = await apiFetch(`/api/reports/profit-analysis${q}`).catch(()=>null);
            if (pa?.profit_by_period && manager.profitChart) {
                const labels = pa.profit_by_period.map(p=>p.period);
                const profits = pa.profit_by_period.map(p=>p.profit || 0);
                const ok = safeUpdate(manager.profitChart, ch => { ch.data.labels = labels; ch.data.datasets[0].data = profits; });
                if (!ok) {
                    manager.profitChart = await recreateOnCanvas('profitOverTimeChart', (c)=> new Chart(c, { type:'line', data:{ labels: labels, datasets:[{ label:'Profit', data: profits, borderColor:'#10B981', backgroundColor:'rgba(16,185,129,0.08)', fill:true }] }, options:{ animation:false, responsive:true, maintainAspectRatio:false } }));
                }
            }

            // customer analysis
            const ca = await apiFetch(`/api/reports/customer-analysis${q}`).catch(()=>null);
            if (ca?.customers && manager.customerChart) {
                const top = (ca.customers || []).slice(0,10);
                const labels = top.map(c=>c.name||c.id);
                const vals = top.map(c=>c.lifetime_value || c.orders_count || 0);
                const ok = safeUpdate(manager.customerChart, ch => { ch.data.labels = labels; ch.data.datasets[0].data = vals; });
                if (!ok) {
                    manager.customerChart = await recreateOnCanvas('customerLTVChart', (c)=> new Chart(c, { type:'bar', data:{ labels: labels, datasets:[{ label:'LTV', data: vals, backgroundColor:'#F59E0B' }] }, options:{ animation:false, responsive:true, maintainAspectRatio:false } }));
                }
            }
        } catch (e) {
            console.error('reports-charts updateAll error', e);
        }
    }

    // expose (include scheduler)
    window.ReportsCharts = { init, updateAll, scheduleUpdateReportsCharts };
        // scheduling: debounce + minimum interval between actual runs
        let _reportsUpdateTimer = null;
        let _reportsLastTs = 0;
        const _reportsDebounce = 250; // ms
        const _reportsMinInterval = 700; // ms

        async function _doScheduledUpdate(manager) {
            _reportsUpdateTimer = null;
            const now = Date.now();
            if (now - _reportsLastTs < _reportsMinInterval) {
                // reschedule to satisfy min interval
                const wait = _reportsMinInterval - (now - _reportsLastTs) + 20;
                _reportsUpdateTimer = setTimeout(()=> _doScheduledUpdate(manager), wait);
                return;
            }
            _reportsLastTs = Date.now();
            await updateAll(manager);
        }

        function scheduleUpdateReportsCharts(manager, forceImmediate=false) {
            if (forceImmediate) {
                if (_reportsUpdateTimer) { clearTimeout(_reportsUpdateTimer); _reportsUpdateTimer = null; }
                return _doScheduledUpdate(manager);
            }
            if (_reportsUpdateTimer) clearTimeout(_reportsUpdateTimer);
            _reportsUpdateTimer = setTimeout(()=> _doScheduledUpdate(manager), _reportsDebounce);
        }

        return { init, updateAll, scheduleUpdateReportsCharts };
})();
