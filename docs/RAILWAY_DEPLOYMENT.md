# Déploiement Railway — Variables d'environnement

## Variables obligatoires

| Variable | Description | Exemple |
|----------|-------------|---------|
| `SECRET_KEY` | Clé secrète Django (longue chaîne aléatoire) | `django-insecure-xxxx...` |
| `DEBUG` | Mode debug | `False` |
| `DJANGO_SETTINGS_MODULE` | Module de settings à utiliser | `config.settings.production` |
| `ALLOWED_HOSTS` | Domaines autorisés (séparés par virgule) | `ton-app.up.railway.app,maketpeyizan.ht` |
| `DATABASE_URL` | URL PostgreSQL (injecté automatiquement par Railway) | `postgresql://user:pass@host/db` |
| `CSRF_TRUSTED_ORIGINS` | Origines CSRF (séparées par virgule) | `https://ton-app.up.railway.app` |

## Services externes

| Variable | Description | Où la trouver |
|----------|-------------|---------------|
| `RESEND_API_KEY` | Clé API pour l'envoi d'emails | [resend.com](https://resend.com) → API Keys |
| `DEFAULT_FROM_EMAIL` | Adresse expéditeur des emails | `Makèt Peyizan <info@maketpeyizan.ht>` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | JSON du service account Firebase (contenu brut) | Firebase Console → Project Settings → Service Accounts |

## Paiements

| Variable | Description |
|----------|-------------|
| `MONCASH_CLIENT_ID` | Client ID MonCash (Digicel) |
| `MONCASH_SECRET_KEY` | Secret Key MonCash |
| `MONCASH_ENVIRONMENT` | `sandbox` ou `production` |
| `PLOPPLOP_CLIENT_ID` | Client ID Plopplop Gateway |

## Nouvelles variables (ajoutées lors de l'audit)

### Sentry — Monitoring d'erreurs (recommandé)
```
SENTRY_DSN = https://xxxxxxxx@oxxxxxxx.ingest.sentry.io/xxxxxxx
```
1. Créer un compte sur [sentry.io](https://sentry.io) (gratuit)
2. Créer un projet de type **Django**
3. Copier le DSN depuis **Settings → Projects → ton projet → Client Keys (DSN)**

> Si `SENTRY_DSN` n'est pas défini, Sentry est simplement désactivé — aucune erreur.

### Redis — Cache (optionnel mais recommandé)
Dans le dashboard Railway de ton projet :
1. Cliquer sur **`+ New`**
2. Sélectionner **`Database → Add Redis`**
3. Railway injecte automatiquement `REDIS_URL` dans ton service — rien d'autre à faire.

> Si `REDIS_URL` n'est pas défini, le cache bascule automatiquement sur la mémoire locale.

## Variables optionnelles

| Variable | Description | Défaut |
|----------|-------------|--------|
| `SITE_URL` | URL publique du site | `https://maketpeyizan.ht` |
| `CORS_ALLOW_ALL` | Autoriser toutes les origines CORS | `False` en prod |
| `CORS_ALLOWED_ORIGINS` | Origines CORS autorisées | — |
| `ADMINS_NOTIFY` | Email admin pour notifications | — |

## Commande de build Railway

Dans `railway.toml` ou les settings Railway, la commande de build doit être :
```
python manage.py migrate && python manage.py collectstatic --noinput
```

Et la commande de démarrage :
```
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --worker-class gthread --threads 4
```
