// Notification Bell UI and logic for fetching and displaying notifications
// Requires: apiFetch (from common.js)

document.addEventListener('DOMContentLoaded', function() {
    const bell = document.getElementById('notificationBell');
    const badge = document.getElementById('notificationBadge');
    const dropdown = document.getElementById('notificationDropdown');
    if (!bell || !badge || !dropdown) return;

    function getIconAndStyle(type) {
        switch(type) {
            case 'sale': return {icon: 'fa-cash-register', color: 'text-green-700', bg: 'bg-green-100'};
            case 'low_stock': return {icon: 'fa-box-open', color: 'text-yellow-800', bg: 'bg-yellow-100'};
            case 'stock_rupture': return {icon: 'fa-times-circle', color: 'text-red-700', bg: 'bg-red-100'};
            case 'product_added': return {icon: 'fa-plus-circle', color: 'text-blue-700', bg: 'bg-blue-100'};
            case 'payment_delay': return {icon: 'fa-clock', color: 'text-orange-700', bg: 'bg-orange-100'};
            default: return {icon: 'fa-info-circle', color: 'text-blue-700', bg: 'bg-gray-100'};
        }
    }

    function fetchNotifications() {
        apiFetch('/api/notifications?unread=1&limit=10')
            .then(data => {
                const notifications = data.notifications || [];
                if (notifications.length > 0) {
                    badge.textContent = notifications.length;
                    badge.style.display = '';
                } else {
                    badge.textContent = '';
                    badge.style.display = 'none';
                }
                dropdown.innerHTML = '';
                if (notifications.length === 0) {
                    dropdown.innerHTML = '<div class="px-4 py-2 text-gray-500">Aucune notification</div>';
                } else {
                    notifications.forEach(n => {
                        const {icon, color, bg} = getIconAndStyle(n.type);
                        const item = document.createElement('div');
                        item.className = `px-4 py-2 mb-1 rounded hover:bg-opacity-80 cursor-pointer flex items-center font-semibold ${bg}`;
                        item.innerHTML = `<span class='mr-2'><i class='fa ${icon} ${color}'></i></span><span class='font-bold ${color}'>${n.message}</span>`;
                        item.onclick = function() {
                            apiFetch(`/api/notifications/${n.id}/read`, {method: 'POST'})
                                .then(() => {
                                    if (n.url) window.location.href = n.url;
                                    else item.classList.add('line-through');
                                    fetchNotifications();
                                });
                        };
                        dropdown.appendChild(item);
                    });
                }
            })
            .catch(() => {
                badge.textContent = '';
                badge.style.display = 'none';
                dropdown.innerHTML = '<div class="px-4 py-2 text-red-500">Erreur de notifications</div>';
            });
    }

    bell.addEventListener('click', function(e) {
        dropdown.classList.toggle('hidden');
        if (!dropdown.classList.contains('hidden')) {
            fetchNotifications();
        }
    });

    // Poll for new notifications every 5 seconds for near real-time updates
    setInterval(fetchNotifications, 5000);
    fetchNotifications();
});
