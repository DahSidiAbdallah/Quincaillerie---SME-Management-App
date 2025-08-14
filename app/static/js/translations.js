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
        login_error_connection: "Erreur de connexion. Vérifiez votre connexion internet."
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
        nav_customers: "👥 العملاء",
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
        login_error_connection: "خطأ في تسجيل الدخول. تحقق من اتصالك بالإنترنت."
    }
};

window.currentLang = document.documentElement.lang || 'fr';

function t(key) {
    const langDict = window.translations[window.currentLang] || {};
    return langDict[key] || key;
}

function applyTranslations(lang) {
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
}

window.t = t;
window.applyTranslations = applyTranslations;
