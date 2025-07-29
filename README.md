# 🔧 Quincaillerie & SME Management App

Une application complète de gestion pour quincailleries et PME avec intelligence artificielle, fonctionnalités hors ligne et architecture moderne.

## 🚀 Installation Rapide

### Option 1: Installation Automatique
```bash
# Cloner ou télécharger le projet
cd "Quincaillerie & SME Management App"

# Exécuter le script d'installation
python setup.py
```

### Option 2: Installation Manuelle

1. **Installer les dépendances**
```bash
pip install -r requirements-minimal.txt
```

2. **Initialiser l'application**
```bash
cd app
python app.py
```

3. **Ouvrir dans le navigateur**
```
http://localhost:5000
```

4. **Connexion par défaut**
- **Utilisateur:** admin
- **PIN:** 1234

## 📋 Configuration Requise

- **Python:** 3.8 ou supérieur
- **Système:** Windows, macOS, Linux
- **Mémoire:** 512 MB RAM minimum
- **Espace disque:** 100 MB minimum

## 🏗️ Structure du Projet

```
Quincaillerie & SME Management App/
├── app/
│   ├── app.py                 # Application principale Flask
│   ├── db/
│   │   └── database.py        # Gestion base de données
│   ├── api/                   # APIs REST
│   │   ├── auth.py           # Authentification
│   │   ├── inventory.py      # Inventaire
│   │   ├── sales.py          # Ventes
│   │   ├── finance.py        # Finances
│   │   ├── reports.py        # Rapports
│   │   └── ai_insights.py    # IA et prédictions
│   ├── models/
│   │   └── ml_forecasting.py # Modèles d'IA
│   ├── offline/
│   │   └── sync_manager.py   # Synchronisation hors ligne
│   ├── templates/            # Templates HTML
│   │   ├── base.html        # Template de base
│   │   ├── login.html       # Page de connexion
│   │   ├── dashboard.html   # Tableau de bord
│   │   └── inventory.html   # Gestion inventaire
│   └── static/              # Fichiers statiques
│       ├── sw.js           # Service Worker (PWA)
│       └── manifest.json   # Manifest PWA
├── requirements.txt         # Dépendances complètes
├── requirements-minimal.txt # Dépendances essentielles
└── setup.py                # Script d'installation
```

## ✨ Fonctionnalités

### 📊 **Phase 1: Inventaire & Ventes**
- ✅ Gestion complète des produits
- ✅ Suivi des stocks avec alertes
- ✅ Point de vente (POS)
- ✅ Scanner de codes-barres

### 💰 **Phase 2: Crédit & Dettes**
- ✅ Gestion des crédits clients
- ✅ Suivi des dettes fournisseurs
- ✅ Rappels de paiement automatiques

### 📈 **Phase 3: Tableau de Bord & Rapports**
- ✅ Tableau de bord en temps réel
- ✅ Rapports avancés avec graphiques
- ✅ Export Excel/PDF

### 🤖 **Phase 4: Intelligence Artificielle**
- ✅ Prédictions de ventes
- ✅ Optimisation des stocks
- ✅ Recommandations intelligentes

### 🔍 **Phase 5: Audit & Notifications**
- ✅ Journalisation complète
- ✅ Notifications en temps réel
- ✅ Suivi des activités

### 🚀 **Phase 6: Assistant IA & Fonctionnalités Avancées**
- ✅ Assistant IA intégré
- ✅ Optimisation des prix
- ✅ Support multilingue (Français/Arabe)

## 📱 **Fonctionnalités Techniques**

### 🌐 **PWA (Progressive Web App)**
- ✅ Installation sur mobile/desktop
- ✅ Fonctionnement hors ligne
- ✅ Synchronisation automatique
- ✅ Notifications push

### 🔒 **Sécurité**
- ✅ Authentification par PIN
- ✅ Contrôle d'accès par rôles
- ✅ Chiffrement des données
- ✅ Audit complet

### 🌍 **Multilingue**
- ✅ Français (principal)
- ✅ Arabe (RTL support)
- ✅ Anglais (optionnel)

## 🔧 Développement

### Démarrer en mode développement
```bash
cd app
python app.py
```

### Tester l'application
```bash
cd app
python -m pytest tests/
```

### Créer une sauvegarde
```bash
cd app
python -c "from db.database import DatabaseManager; DatabaseManager().backup_database()"
```

## 🚀 Déploiement Production

### Avec Gunicorn (Linux/macOS)
```bash
cd app
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Avec Waitress (Windows)
```bash
cd app
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

## 📞 Support

- **Auteur:** Dah Sidi Abdallah
- **Date:** 24 Juillet 2025
- **Version:** 1.0.0

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

---

🎉 **Félicitations!** Votre application de gestion de quincaillerie est maintenant prête à utiliser!
