// Lightweight helper to ensure Chart.js and Alpine components initialize correctly
(function(){
    // Wait for DOM ready
    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }

    ready(function(){
        // Ensure Alpine is present (base.html loads CDN-deferred). If not, nothing to do here.
        if (!window.Alpine) {
            console.warn('Alpine.js not found on reports page. Many interactive features may not work.');
        }

        // Provide fallback: if Chart is not present, attempt to load local file chart. If local file missing, load CDN
        function loadScript(src, cb){
            var s = document.createElement('script');
            s.src = src; s.async = true; s.onload = cb; s.onerror = cb;
            document.head.appendChild(s);
        }

        // Try local first (bundled file), then CDN
        var chartLocal = '/static/js/chart.umd.min.js';
        // check existence by attempting to fetch (lightweight)
        fetch(chartLocal, {method: 'HEAD'}).then(function(resp){
            if (resp.ok) {
                loadScript(chartLocal, function(){ console.log('Loaded local Chart.js'); });
            } else {
                loadScript('https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js', function(){ console.log('Loaded Chart.js from CDN'); });
            }
        }).catch(function(){
            loadScript('https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js', function(){ console.log('Loaded Chart.js from CDN (fallback)'); });
        });

        // Accessibility: ensure report type buttons have click handlers if Alpine not available
        if (!window.Alpine) {
            document.querySelectorAll('[data-report-type]').forEach(function(btn){
                btn.addEventListener('click', function(){
                    // Simple fallback: change window.location with tab query
                    var t = btn.getAttribute('data-report-type');
                    var url = new URL(window.location.href);
                    url.searchParams.set('tab', t);
                    window.location.href = url.toString();
                });
            });
        }
    });
})();
