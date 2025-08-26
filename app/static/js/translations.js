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
    dashboard_optimize: "Optimiser →",
    login_page_title: "Connexion - SME Management",
    dashboard_page_title: "Tableau de Bord - SME Management",
    inventory_page_title: "Gestion d'Inventaire - SME Management",
    inventory_header: "Gestion d'Inventaire",
    inventory_description: "Gérez vos produits, stock et approvisionnements",
    inventory_add_product: "Ajouter Produit",
    inventory_import_export: "Import/Export",
    inventory_export_inventory: "📤 Exporter Inventaire",
    inventory_import_products: "📥 Importer Produits",
    inventory_report_inventory: "📊 Rapport d'Inventaire",
    inventory_actions: "Actions",
    inventory_count: "🔢 Comptage d'Inventaire",
    inventory_batch_operations: "📋 Opérations par Lot",
    inventory_history: "📜 Historique d'Inventaire",
    inventory_total_products: "Total Produits",
    sales_page_title: "Gestion des Ventes - SME Management",
    sales_today: "Ventes Aujourd'hui",
    sales_active_customers: "Clients Actifs",
    sales_pending: "En Attente",
    sales_monthly_revenue: "Revenus Mensuel",
    sales_status_all: "Tous les statuts",
    sales_status_paid: "Payé",
    sales_status_pending: "En attente",
    sales_status_retard: "Retard",
    sales_status_cancelled: "Annulé",
    sales_table_id: "ID",
    sales_table_customer: "Client",
    sales_table_date: "Date",
    sales_table_amount: "Montant",
    sales_table_payment_method: "Mode Paiement",
    sales_table_status: "Statut",
    sales_table_actions: "Actions",
    sales_table_product: "Produit",
    sales_table_quantity: "Quantité",
    sales_table_unit_price: "Prix Unitaire",
    sales_table_total: "Total",
    sales_no_sales: "Aucune vente trouvée",
    sales_form_customer: "Client",
    sales_form_select_customer: "Sélectionner un client",
    sales_browse_customers: "Parcourir les clients",
    sales_form_payment_method: "Mode de Paiement",
    sales_payment_cash: "Espèces",
    sales_payment_card: "Carte",
    sales_payment_check: "Chèque",
    sales_payment_credit: "Crédit",
    sales_form_due_date: "Date d'échéance",
    sales_form_products: "Produits",
    sales_form_select_product: "Sélectionner un produit",
    sales_form_quantity: "Quantité",
    sales_form_total: "Total:",
    sales_cancel: "Annuler",
    sales_create: "Créer la Vente",
    sales_customer_list: "Liste des Clients",
    sales_manage_customers: "Gérer les clients dans la page dédiée",
    sales_search_customer_placeholder: "Rechercher un client (nom, téléphone)",
    sales_customer_name: "Nom",
    sales_customer_phone: "Téléphone",
    sales_select: "Sélectionner",
    sales_no_customers: "Aucun client",
    sales_edit_sale: "Modifier la Vente",
    sales_form_due_date_credit: "Date d'échéance (crédit)",
    sales_form_notes: "Notes",
    sales_save: "Enregistrer",
    sales_view_sale: "Détails de la Vente",
    sales_paid: "Payé:",
    sales_credit_remaining: "Crédit restant:",
    sales_delete_sale: "Supprimer la vente",
    sales_delete_confirm: "Êtes-vous sûr de vouloir supprimer la vente ? Cette action va restaurer le stock.",
    sales_delete: "Supprimer",
    sales_mark_paid: "Marquer payé",
    sales_header: "Gestion des Ventes",
    sales_description: "Gérez vos transactions, clients et paiements",
    sales_new_sale: "Nouvelle Vente",
    sales_view_customers: "Voir Clients",
    sales_report: "Rapport de Ventes",
    sales_export: "Exporter",
    sales_all_sales: "Toutes les Ventes",
    customers_page_title: "Clients - SME Management",
    customers_header: "Gestion des Clients",
    customers_description: "Gérez vos clients pour les ventes et le suivi des crédits",
    customers_new_customer: "Nouveau Client",
    customers_export: "Exporter",
    customers_list: "Liste des Clients",
    customers_search_placeholder: "Rechercher...",
    customers_empty_search: "Aucun client ne correspond à votre recherche.",
    customers_empty: "Aucun client enregistré. Ajoutez votre premier client!",
    customers_add_first: "Ajouter un client",
    finance_page_title: "Finance - SME Management",
    finance_header: "Gestion Financière",
    finance_description: "Suivez vos revenus, dépenses et performance financière",
    finance_tab_summary: "Résumé",
    finance_tab_receivables: "Créances en retard",
    finance_new_transaction: "Nouvelle Transaction",
    finance_new_expense: "Nouvelle Dépense",
    finance_report: "Rapport Financier",
    finance_backup: "Sauvegarde",
    finance_diagnose_charts: "Diagnostiquer Graphiques",
    reports_page_title: "Rapports - SME Management",
    reports_header: "Rapports et Analytics",
    reports_description: "Analysez vos performances et générez des rapports détaillés",
    reports_types: "Types de Rapports",
    reports_filters: "Filtres de Rapport",
    reports_generate_report: "Générer Rapport"
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
    dashboard_optimize: "تحسين →",
    login_page_title: "تسجيل الدخول - إدارة المتجر",
    dashboard_page_title: "لوحة التحكم - إدارة المتجر",
    inventory_page_title: "إدارة المخزون - إدارة المتجر",
    inventory_header: "إدارة المخزون",
    inventory_description: "إدارة المنتجات والمخزون والتوريد",
    inventory_add_product: "إضافة منتج",
    inventory_import_export: "استيراد/تصدير",
    inventory_export_inventory: "📤 تصدير المخزون",
    inventory_import_products: "📥 استيراد المنتجات",
    inventory_report_inventory: "📊 تقرير المخزون",
    inventory_actions: "إجراءات",
    inventory_count: "🔢 جرد المخزون",
    inventory_batch_operations: "📋 عمليات مجمعة",
    inventory_history: "📜 تاريخ المخزون",
    inventory_total_products: "إجمالي المنتجات",
    sales_page_title: "إدارة المبيعات - إدارة المتجر",
    sales_today: "مبيعات اليوم",
    sales_active_customers: "العملاء النشطون",
    sales_pending: "قيد الانتظار",
    sales_monthly_revenue: "الإيرادات الشهرية",
    sales_status_all: "كل الحالات",
    sales_status_paid: "مدفوع",
    sales_status_pending: "قيد الانتظار",
    sales_status_retard: "متأخر",
    sales_status_cancelled: "ملغى",
    sales_table_id: "المعرف",
    sales_table_customer: "العميل",
    sales_table_date: "التاريخ",
    sales_table_amount: "المبلغ",
    sales_table_payment_method: "طريقة الدفع",
    sales_table_status: "الحالة",
    sales_table_actions: "إجراءات",
    sales_table_product: "المنتج",
    sales_table_quantity: "الكمية",
    sales_table_unit_price: "سعر الوحدة",
    sales_table_total: "الإجمالي",
    sales_no_sales: "لا توجد مبيعات",
    sales_form_customer: "العميل",
    sales_form_select_customer: "اختر عميلاً",
    sales_browse_customers: "تصفح العملاء",
    sales_form_payment_method: "طريقة الدفع",
    sales_payment_cash: "نقداً",
    sales_payment_card: "بطاقة",
    sales_payment_check: "شيك",
    sales_payment_credit: "ائتمان",
    sales_form_due_date: "تاريخ الاستحقاق",
    sales_form_products: "المنتجات",
    sales_form_select_product: "اختر منتجاً",
    sales_form_quantity: "الكمية",
    sales_form_total: ":الإجمالي",
    sales_cancel: "إلغاء",
    sales_create: "إنشاء عملية البيع",
    sales_customer_list: "قائمة العملاء",
    sales_manage_customers: "إدارة العملاء في الصفحة المخصصة",
    sales_search_customer_placeholder: "ابحث عن عميل (الاسم، الهاتف)",
    sales_customer_name: "الاسم",
    sales_customer_phone: "الهاتف",
    sales_select: "اختيار",
    sales_no_customers: "لا يوجد عملاء",
    sales_edit_sale: "تعديل البيع",
    sales_form_due_date_credit: "تاريخ الاستحقاق (ائتمان)",
    sales_form_notes: "ملاحظات",
    sales_save: "حفظ",
    sales_view_sale: "تفاصيل البيع",
    sales_paid: ":مدفوع",
    sales_credit_remaining: ":المتبقي من الائتمان",
    sales_delete_sale: "حذف البيع",
    sales_delete_confirm: "هل أنت متأكد أنك تريد حذف عملية البيع؟ سيؤدي ذلك إلى استعادة المخزون.",
    sales_delete: "حذف",
    sales_mark_paid: "تحديد كمدفوع",
    sales_header: "إدارة المبيعات",
    sales_description: "إدارة المعاملات والزبناء والمدفوعات",
    sales_new_sale: "عملية بيع جديدة",
    sales_view_customers: "عرض الزبناء",
    sales_report: "تقرير المبيعات",
    sales_export: "تصدير",
    sales_all_sales: "جميع المبيعات",
    customers_page_title: "الزبناء - إدارة المتجر",
    customers_header: "إدارة الزبناء",
    customers_description: "إدارة الزبناء للمبيعات ومتابعة الديون",
    customers_new_customer: "زبون جديد",
    customers_export: "تصدير",
    customers_list: "قائمة الزبناء",
    customers_search_placeholder: "بحث...",
    customers_empty_search: "لا يوجد زبون يطابق بحثك.",
    customers_empty: "لا يوجد زبون مسجل. أضف أول زبون!",
    customers_add_first: "إضافة زبون",
    finance_page_title: "المالية - إدارة المتجر",
    finance_header: "الإدارة المالية",
    finance_description: "تابع الإيرادات والمصروفات والأداء المالي",
    finance_tab_summary: "ملخص",
    finance_tab_receivables: "الديون المتأخرة",
    finance_new_transaction: "معاملة جديدة",
    finance_new_expense: "مصروف جديد",
    finance_report: "تقرير مالي",
    finance_backup: "نسخة احتياطية",
    finance_diagnose_charts: "تشخيص الرسوم",
    reports_page_title: "التقارير - إدارة المتجر",
    reports_header: "التقارير والتحليلات",
    reports_description: "حلل الأداء وأنشئ تقارير مفصلة",
    reports_types: "أنواع التقارير",
    reports_filters: "مرشحات التقرير",
    reports_generate_report: "إنشاء تقرير"
    }
};


// Add a loading overlay for language switching UX
if (!document.getElementById('lang-loading-overlay')) {
    (function createLangOverlay() {
        const attach = () => {
            try {
                if (document.getElementById('lang-loading-overlay')) return;
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
                overlay.innerHTML = `
                    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:2rem;color:#333;">
                        <span class="lang-spinner" style="display:inline-block;width:2rem;height:2rem;border:3px solid #ccc;border-top:3px solid #333;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:1rem;"></span>
                        <div id="lang-loading-text">Loading...</div>
                    </div>
                `;
                if (document.body) document.body.appendChild(overlay);
                // Add spinner animation
                const style = document.createElement('style');
                style.textContent = `@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
                if (document.head) document.head.appendChild(style);
            } catch (err) {
                // If DOM isn't ready, schedule for DOMContentLoaded
                try { window.addEventListener && window.addEventListener('DOMContentLoaded', attach); } catch (e) { /* ignore */ }
            }
        };
        attach();
    })();
}


// Get language from localStorage if available, else from <html lang>, else default to 'fr'
function getStoredLang() {
    try {
        const stored = localStorage.getItem('app_language');
        if (stored && (stored === 'fr' || stored === 'ar')) return stored;
    } catch (e) {}
    return document.documentElement.lang || 'fr';
}

window.currentLang = getStoredLang();

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
            try { localStorage.setItem('app_language', lang); } catch (e) {}
        } else {
            // If no lang provided, use stored or default
            window.currentLang = getStoredLang();
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
