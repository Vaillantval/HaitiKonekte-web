# AyitiKonekte 🛍️

**La Marketplace Haïtienne** — La plateforme qui connecte vendeurs et acheteurs partout en Haïti.

---

## À propos

**AyitiKonekte** est une plateforme web full-stack conçue pour digitaliser le commerce haïtien. Elle met en relation vendeurs locaux, acheteurs (particuliers, grossistes, restaurants, institutions) et agents logistiques, avec un accent sur la traçabilité des produits, la flexibilité des paiements et l'accessibilité mobile.

Toutes catégories de produits sont acceptées : alimentaire, artisanat, électronique, vêtements, services, et plus encore.

### Rôles utilisateurs

| Rôle | Description |
|------|-------------|
| **Vendeur** | Gère son catalogue, ses stocks et ses commandes |
| **Acheteur** | Particulier, grossiste, coopérative ou institution |
| **Collecteur** | Agent logistique coordonnant les collectes terrain |
| **Super-Admin** | Gestionnaire de la plateforme avec accès BI complet |

---

## Fonctionnalités

### Pour les vendeurs
- Gestion du catalogue produits avec photos et QR codes générés automatiquement
- Tarification unitaire et en gros (prix de détail / prix grossiste)
- Gestion des stocks par lot (dates, alertes de seuil)
- Suivi des commandes reçues et mise à jour des statuts
- Participation aux collectes planifiées
- Tableau de bord avec statistiques de ventes et revenus
- Export des rapports en PDF et CSV

### Pour les acheteurs
- Navigation dans le catalogue (filtres par catégorie, localisation, disponibilité)
- Panier persistant multi-vendeurs (session anonyme ou base de données)
- Checkout avec choix du mode de livraison (domicile / retrait / collecte)
- 6 modes de paiement : MonCash, NatCash, virement, cash, e-voucher, hors-ligne
- Suivi des commandes en temps réel avec notifications push
- Gestion des adresses de livraison multiples
- Système de vouchers et bons de réduction (programmes ONG, coopératives, entreprises)

### Pour les administrateurs
- Interface d'administration Jazzmin (Django Admin stylisé — thème Bleu/Rouge)
- Gestion complète des utilisateurs, produits, commandes, paiements
- Tableau de bord analytique (KPIs, ventes, top produits/vendeurs)
- Export des données en PDF et Excel
- Configuration du site (logo, textes, réseaux sociaux, mode maintenance)
- Gestion des FAQ et messages de contact avec réponse par email
- Carte géographique des utilisateurs (Leaflet)

### Système
- Notifications push Firebase (FCM) — topics par rôle
- Emails transactionnels via Resend
- API REST complète documentée (Swagger UI / ReDoc)
- Rate limiting (throttling DRF) sur tous les endpoints
- Cache backend configurable (mémoire locale ou Redis)
- Logging structuré + monitoring Sentry (production)
- Support multilingue : Français, Kreyòl ayisyen, English, Español
- Fuseau horaire : America/Port-au-Prince
- Tests unitaires (accounts, catalog, orders)

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Framework | Django 5.2, Django REST Framework 3.15 |
| **Langage** | **Python 3.13** |
| Base de données | PostgreSQL (production), SQLite (développement) |
| Authentification | JWT via SimpleJWT (access 1j, refresh 30j, blacklist) |
| Admin UI | Jazzmin — thème Bleu marine / Rouge |
| Fichiers statiques | WhiteNoise (compression + serving) |
| Notifications push | Firebase Admin SDK (FCM) |
| Emails | Resend API |
| Paiements | Plopplop Gateway (MonCash, NatCash) |
| PDF / Excel | ReportLab, openpyxl |
| QR Codes | qrcode[pil] |
| Cache | Mémoire locale (dev) / Redis (prod) |
| Rate limiting | DRF Throttling (200/h anon, 2000/h user) |
| Monitoring | Sentry SDK (production) |
| Serveur WSGI | Gunicorn (3 workers, 4 threads gthread) |
| Déploiement | Docker + Railway |
| Documentation API | drf-spectacular (OpenAPI 3 / Swagger) |

---

## Architecture

```
ayiti-konekte/
├── config/                  # Configuration Django (settings base/dev/prod, urls, wsgi)
├── apps/
│   ├── accounts/            # Utilisateurs, profils Vendeur & Acheteur, adresses
│   ├── catalog/             # Produits, catégories, images, QR codes
│   ├── orders/              # Panier hybride, commandes, lignes de commande
│   ├── payments/            # Paiements, vouchers, intégration Plopplop/MonCash
│   ├── stock/               # Lots, mouvements de stock, alertes
│   ├── collectes/           # Zones, points, événements de collecte, participations
│   ├── analytics/           # Tableau de bord BI super-admin (PDF, Excel)
│   ├── core/                # Configuration site singleton, FAQ, messages de contact
│   ├── emails/              # Service email (Resend) + notifications FCM
│   ├── home/                # Pages publiques et tableaux de bord utilisateurs
│   ├── geo/                 # Données géographiques (départements, communes)
│   └── api_admin/           # Endpoints API réservés aux administrateurs
├── templates/               # Templates HTML (Django Template Language)
├── static/                  # CSS, JS, images statiques
├── media/                   # Fichiers uploadés (images, QR codes, preuves)
├── locale/                  # Fichiers de traduction (.po / .mo)
├── requirements/
│   ├── base.txt             # Django, DRF, Pillow, Firebase, Resend…
│   ├── development.txt      # + debug-toolbar, ipython
│   └── production.txt       # + sentry-sdk, redis
├── docs/                    # Documentation (API, Railway, Flutter)
├── Dockerfile               # Image python:3.13-slim
├── railway.toml             # Configuration déploiement Railway
└── init_site.py             # Création automatique du super-admin au démarrage
```

---

## Installation locale

### Prérequis

> **Python 3.13** est requis (Django 5.2 exige Python 3.10 minimum).
> Télécharge Python 3.13 sur [python.org/downloads](https://www.python.org/downloads/).

```bash
# Vérifier la version
python --version   # doit afficher Python 3.13.x
```

### Étapes

```bash
# Cloner le dépôt
git clone https://github.com/Vaillantval/MAKET-PYIZAN-Transversal.git
cd MAKET-PYIZAN-Transversal

# Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Installer les dépendances de développement
pip install -r requirements/development.txt

# Configurer les variables d'environnement
cp .env.example .env            # puis éditer .env selon votre config

# Appliquer les migrations
python manage.py migrate

# Compiler les messages i18n
python manage.py compilemessages

# (Optionnel) Lancer les tests
python manage.py test apps.accounts apps.catalog apps.orders

# Lancer le serveur de développement
python manage.py runserver
```

L'application sera accessible sur [http://localhost:8000](http://localhost:8000).  
L'admin Django : [http://localhost:8000/admin/](http://localhost:8000/admin/)  
La documentation API : [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)

---

## Déploiement (Railway)

L'application est déployée sur [Railway](https://railway.app) avec :
- **Base de données :** PostgreSQL (service Railway dédié)
- **Cache :** Redis (service Railway optionnel — détecté via `REDIS_URL`)
- **Volume persistant :** monté sur `/app/media` pour les fichiers uploadés
- **Build :** Dockerfile (`python:3.13-slim`)

### Séquence de démarrage automatique

```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py compilemessages
python init_site.py
gunicorn config.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 3 --threads 4 \
  --worker-class gthread \
  --timeout 120
```

### Variables d'environnement Railway

| Variable | Obligatoire | Description |
|----------|:-----------:|-------------|
| `SECRET_KEY` | ✅ | Clé secrète Django |
| `DEBUG` | ✅ | `False` en production |
| `DJANGO_SETTINGS_MODULE` | ✅ | `config.settings.production` |
| `ALLOWED_HOSTS` | ✅ | Domaines autorisés (virgule-séparés) |
| `DATABASE_URL` | ✅ | URL PostgreSQL (injecté automatiquement par Railway) |
| `CSRF_TRUSTED_ORIGINS` | ✅ | Ex: `https://ayitikonekte.ht` |
| `RESEND_API_KEY` | ✅ | Clé API Resend pour les emails |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | ✅ | JSON credentials Firebase (FCM) |
| `MONCASH_CLIENT_ID` | ✅ | Client ID MonCash |
| `MONCASH_SECRET_KEY` | ✅ | Secret Key MonCash |
| `MONCASH_ENVIRONMENT` | ✅ | `sandbox` ou `production` |
| `PLOPPLOP_CLIENT_ID` | — | Client ID gateway Plopplop |
| `SENTRY_DSN` | — | DSN Sentry pour le monitoring d'erreurs |
| `REDIS_URL` | — | URL Redis (injecté par Railway si service Redis ajouté) |
| `SITE_URL` | — | URL publique du site |
| `SUPERADMIN_USERNAME` | — | Username du super-admin initial |
| `SUPERADMIN_EMAIL` | — | Email du super-admin initial |
| `SUPERADMIN_PASSWORD` | — | Mot de passe du super-admin initial |

> Ne jamais committer ces variables dans le code — les gérer uniquement dans le dashboard Railway.

---

## Endpoints API principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/auth/register/` | Inscription |
| `POST` | `/api/auth/login/` | Connexion (retourne JWT) |
| `GET` | `/api/auth/me/` | Profil utilisateur connecté |
| `GET` | `/api/products/` | Liste des produits (filtres, pagination) |
| `GET` | `/api/products/categories/` | Catégories du catalogue |
| `GET` | `/api/orders/panier/` | Contenu du panier |
| `POST` | `/api/orders/panier/ajouter/` | Ajouter au panier |
| `POST` | `/api/orders/commander/` | Passer une commande |
| `POST` | `/api/payments/initier/` | Initier un paiement |
| `POST` | `/api/payments/preuve/` | Soumettre une preuve de paiement |
| `GET` | `/api/schema/swagger-ui/` | Documentation Swagger complète |
| `GET` | `/health/` | Health check Railway |

---

## Paiements supportés

| Méthode | Description |
|---------|-------------|
| **MonCash** | Paiement mobile Digicel Haiti |
| **NatCash** | Paiement mobile BNC Haiti |
| **Virement bancaire** | Avec soumission de preuve photo |
| **Cash** | Paiement à la livraison |
| **E-Voucher** | Bons de réduction (ONG, coopératives, entreprises) |
| **Hors-ligne** | Paiement convenu hors plateforme |

---

## Tests

```bash
# Lancer tous les tests
python manage.py test apps.accounts apps.catalog apps.orders

# Avec verbosité
python manage.py test apps.accounts apps.catalog apps.orders -v 2
```

Couverture actuelle :
- `apps/accounts/tests.py` — Inscription, login, profil, adresses
- `apps/catalog/tests.py` — Liste produits, filtres, détail, catégories
- `apps/orders/tests.py` — CartService complet (session + DB)

---

## Palette couleurs

| Rôle | Couleur | Hex |
|------|---------|-----|
| Primaire | Bleu marine | `#003F87` |
| Sombre | Bleu nuit | `#002B5E` |
| Intermédiaire | Bleu moyen | `#1565C0` |
| Fond léger | Bleu pâle | `#EEF4FF` |
| Accent | Rouge haïtien | `#C62828` |
| Accent sombre | Rouge profond | `#8E0000` |

---

## Licence

Projet propriétaire — Tous droits réservés © AyitiKonekte 2026.
