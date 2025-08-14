// Centralized translation dictionary and helpers
window.translations = {
    fr: {
        app_title: "SME Management",
        system_description: "Système de Gestion - Connectez-vous à votre compte",
        username_label: "Nom d'utilisateur",
        username_placeholder: "Entrez votre nom d'utilisateur",
        pin_label: "Code PIN",
        pin_placeholder: "Entrez votre PIN",
        pin_hint: "PIN par défaut admin: 1234 | Employés: voir administrateur",
        login_button: "Se connecter",
        login_loading: "Connexion...",
        quick_login_title: "Connexion rapide (démonstration):",
        quick_login_admin: "👤 Admin",
        quick_login_employee: "👷 Employé",
        status_online: "En ligne",
        status_offline: "Hors ligne",
        nav_dashboard: "📊 Tableau de bord",
        nav_inventory: "📦 Inventaire",
        nav_sales: "💰 Ventes",
        nav_customers: "👥 Clients",
        nav_finance: "💳 Finance",
        nav_reports: "📈 Rapports",
        nav_admin: "⚙️ Admin",
        settings: "⚙️ Paramètres",
        logout: "🚪 Déconnexion",
        logout_confirm: "Êtes-vous sûr de vouloir vous déconnecter?",
        sync_status: "Synchronisé",
        loading: "Chargement...",
        install_app: "Installer l'application",
        session_expiring: "Votre session va expirer dans 10 secondes. Vous serez déconnecté(e) bientôt.",
        session_expired: "Session expirée. Déconnexion...",
        logout_error: "Erreur lors de la déconnexion",
        mode_admin: "Administrateur",
        mode_employee: "Employé",
        mode_prefix: "Mode:",
        user_prefix: "Utilisateur:",
        login_error: "Erreur de connexion",
    login_error_connection: "Erreur de connexion. Vérifiez votre connexion internet.",
    dashboard_title: "Tableau de bord",
    dashboard_overview: "Vue d'ensemble de votre activité, ventes et inventaire",
    dashboard_total_products: "Total Produits",
    dashboard_low_stock: "Stock Faible",
    dashboard_out_of_stock: "Rupture",
    dashboard_today_sales: "Ventes Aujourd'hui",
    dashboard_total_revenue: "Revenus Total",
    dashboard_sales_7days: "Ventes des 7 Derniers Jours",
    dashboard_sales_daily: "Journalier",
    dashboard_sales_weekly: "Hebdomadaire",
    dashboard_top_products: "Produits les Plus Vendus",
    dashboard_units_sold: "unités vendues",
    dashboard_view_all_products: "Voir tous les produits →",
    dashboard_recent_activities: "Activités Récentes",
    dashboard_no_recent_activity: "Aucune activité récente",
    dashboard_view_more_activities: "Voir plus d'activités →",
    dashboard_alerts_reminders: "Alertes & Rappels",
    dashboard_low_stock_alert: "Stock Faible",
    dashboard_low_stock_below_threshold: "produits sont en dessous du seuil d'alerte.",
    dashboard_view_low_stock_products: "Voir les produits →",
    dashboard_overdue_payments: "Paiements en Retard",
    dashboard_no_overdue_clients: "0 clients ont des paiements en retard",
    dashboard_view_overdue_payments: "Voir les créances →",
    dashboard_system_status: "État du Système",
    dashboard_system_online: "Système en ligne",
    dashboard_last_sync: "Dernière synchronisation: aujourd'hui",
    dashboard_ai_insights: "Insights IA",
    dashboard_ai_recommendations: "Recommandations intelligentes pour votre business",
    dashboard_sales_forecast: "Prédiction de Ventes",
    dashboard_view_details: "Voir détails →",
    dashboard_restock: "Réapprovisionnement",
    dashboard_view_suggestions: "Voir suggestions →",
    dashboard_price_optimization: "Optimisation Prix",
    dashboard_optimize: "Optimiser →"
    },
    ar: {
        app_title: "إدارة المتجر",
        system_description: "نظام إدارة - قم بتسجيل الدخول إلى حسابك",
        username_label: "اسم المستخدم",
        username_placeholder: "أدخل اسم المستخدم",
        pin_label: "رمز PIN",
        pin_placeholder: "أدخل رمز PIN",
        pin_hint: "PIN الافتراضي للمشرف: 1234 | الموظفون: اسأل المدير",
        login_button: "تسجيل الدخول",
        login_loading: "جاري تسجيل الدخول...",
        quick_login_title: "تسجيل سريع (عرض):",
        quick_login_admin: "👤 مشرف",
        quick_login_employee: "👷 موظف",
        status_online: "متصل",
        status_offline: "غير متصل",
        nav_dashboard: "📊 لوحة التحكم",
        nav_inventory: "📦 المخزون",
        nav_sales: "💰 المبيعات",
        nav_customers: "👥 الزبناء",
        nav_finance: "💳 المالية",
        nav_reports: "📈 التقارير",
        nav_admin: "⚙️ الإدارة",
        settings: "⚙️ الإعدادات",
        logout: "🚪 تسجيل الخروج",
        logout_confirm: "هل أنت متأكد أنك تريد تسجيل الخروج؟",
        sync_status: "متزامن",
        loading: "جاري التحميل...",
        install_app: "تثبيت التطبيق",
        session_expiring: "ستنتهي جلستك خلال 10 ثوانٍ. سيتم تسجيل خروجك قريبًا.",
        session_expired: "انتهت الجلسة. جاري تسجيل الخروج...",
        logout_error: "حدث خطأ أثناء تسجيل الخروج",
        mode_admin: "مدير",
        mode_employee: "موظف",
        mode_prefix: "الوضع:",
        user_prefix: "المستخدم:",
        login_error: "خطأ في تسجيل الدخول",
    login_error_connection: "خطأ في تسجيل الدخول. تحقق من اتصالك بالإنترنت.",
    dashboard_title: "لوحة التحكم",
    dashboard_overview: "نظرة عامة على نشاطك، المبيعات والمخزون",
    dashboard_total_products: "إجمالي المنتجات",
    dashboard_low_stock: "مخزون منخفض",
    dashboard_out_of_stock: "نفاد المخزون",
    dashboard_today_sales: "مبيعات اليوم",
    dashboard_total_revenue: "إجمالي الإيرادات",
    dashboard_sales_7days: "مبيعات آخر 7 أيام",
    dashboard_sales_daily: "يومي",
    dashboard_sales_weekly: "أسبوعي",
    dashboard_top_products: "المنتجات الأكثر مبيعًا",
    dashboard_units_sold: "وحدة مباعة",
    dashboard_view_all_products: "عرض كل المنتجات →",
    dashboard_recent_activities: "الأنشطة الأخيرة",
    dashboard_no_recent_activity: "لا توجد أنشطة حديثة",
    dashboard_view_more_activities: "عرض المزيد من الأنشطة →",
    dashboard_alerts_reminders: "تنبيهات وتذكيرات",
    dashboard_low_stock_alert: "مخزون منخفض",
    dashboard_low_stock_below_threshold: "منتجات تحت حد التنبيه.",
    dashboard_view_low_stock_products: "عرض المنتجات →",
    dashboard_overdue_payments: "مدفوعات متأخرة",
    dashboard_no_overdue_clients: "لا يوجد عملاء متأخرون في الدفع",
    dashboard_view_overdue_payments: "عرض الديون →",
    dashboard_system_status: "حالة النظام",
    dashboard_system_online: "النظام متصل",
    dashboard_last_sync: "آخر مزامنة: اليوم",
    dashboard_ai_insights: "رؤى الذكاء الاصطناعي",
    dashboard_ai_recommendations: "توصيات ذكية لعملك",
    dashboard_sales_forecast: "توقعات المبيعات",
    dashboard_view_details: "عرض التفاصيل →",
    dashboard_restock: "إعادة التوريد",
    dashboard_view_suggestions: "عرض الاقتراحات →",
    dashboard_price_optimization: "تحسين الأسعار",
    dashboard_optimize: "تحسين →"
    }
};


// Add a loading overlay for language switching UX
if (!document.getElementById('lang-loading-overlay')) {
    const overlay = document.createElement('div');
    overlay.id = 'lang-loading-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = 0;
    overlay.style.left = 0;
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.background = 'rgba(255,255,255,0.7)';
    overlay.style.display = 'none';
    overlay.style.zIndex = 9999;
    overlay.innerHTML = '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:2rem;color:#333;"><span class="lang-spinner" style="display:inline-block;width:2rem;height:2rem;border:3px solid #ccc;border-top:3px solid #333;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:1rem;"></span><div id="lang-loading-text">Loading...</div></div>';
    document.body.appendChild(overlay);
    // Add spinner animation
    const style = document.createElement('style');
    style.textContent = '@keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}';
    document.head.appendChild(style);
}

window.currentLang = document.documentElement.lang || 'fr';

function t(key) {
    const langDict = window.translations[window.currentLang] || {};
    return langDict[key] || key;
}

function applyTranslations(lang) {
    // Show loading overlay
    const overlay = document.getElementById('lang-loading-overlay');
    if (overlay) {
        overlay.style.display = 'block';
        // Set loading text based on language
        let loadingText = 'Loading...';
        if (lang === 'ar') loadingText = 'جاري التحميل...';
        else if (lang === 'fr') loadingText = 'Chargement...';
        document.getElementById('lang-loading-text').textContent = loadingText;
    }

    setTimeout(() => {
        if (lang) {
            window.currentLang = lang;
        }
        const dir = window.currentLang === 'ar' ? 'rtl' : 'ltr';
        document.documentElement.setAttribute('lang', window.currentLang);
        document.documentElement.setAttribute('dir', dir);

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (key) {
                el.textContent = t(key);
            }
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (key) {
                el.setAttribute('placeholder', t(key));
            }
        });

        // Hide loading overlay after translations are applied
        if (overlay) {
            setTimeout(() => { overlay.style.display = 'none'; }, 350);
        }
    }, 150);
}

window.t = t;
window.applyTranslations = applyTranslations;
