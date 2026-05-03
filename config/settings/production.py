from .base import *
from decouple import config as env
import dj_database_url
import os

DEBUG = False

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

# Railway utilise un reverse-proxy HTTPS (SSL termination).
# Sans cette ligne Django voit HTTP alors que l'Origin header dit https:// → CSRF failure.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Domaines autorisés — mettre l'URL Railway + domaine custom si applicable
# Ex : ALLOWED_HOSTS=maket-peyizan.up.railway.app,maketpeyizan.ht
ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='localhost').split(',')

# Ajout automatique des domaines Railway injectés par la plateforme
# (nécessaire pour que le healthcheck GET /health/ ne soit pas bloqué par Django)
_RAILWAY_SAFE_HOSTS = [
    '0.0.0.0',
    'healthcheck.railway.app',
]
for _h in _RAILWAY_SAFE_HOSTS:
    if _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)

for _var in ('RAILWAY_PUBLIC_DOMAIN', 'RAILWAY_PRIVATE_DOMAIN', 'RAILWAY_STATIC_URL'):
    _domain = os.environ.get(_var, '').strip()
    if _domain and _domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_domain)

# CSRF_TRUSTED_ORIGINS — obligatoire sur Railway (HTTPS proxy)
# Prendre les origines explicites depuis la variable d'env (ex: https://maket.up.railway.app)
_raw_origins = env('CSRF_TRUSTED_ORIGINS', default='')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _raw_origins.split(',') if o.strip()] if _raw_origins else []

# Auto-détecter les domaines Railway et les ajouter avec https://
for _var in ('RAILWAY_PUBLIC_DOMAIN', 'RAILWAY_PRIVATE_DOMAIN'):
    _domain = os.environ.get(_var, '').strip()
    if _domain:
        _origin = f'https://{_domain}'
        if _origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(_origin)

# Ajouter aussi les domaines de ALLOWED_HOSTS qui ressemblent à un vrai domaine
for _h in ALLOWED_HOSTS:
    if _h not in ('localhost', '0.0.0.0', '127.0.0.1', 'healthcheck.railway.app') and '.' in _h:
        for _scheme in ('https://', 'http://'):
            _o = f'{_scheme}{_h}'
            if _o not in CSRF_TRUSTED_ORIGINS:
                CSRF_TRUSTED_ORIGINS.append(_o)

# CORS : en prod mettre les origines Flutter + web
# Ex : CORS_ALLOW_ALL=False  +  CORS_ALLOWED_ORIGINS=https://maketpeyizan.ht
CORS_ALLOW_ALL_ORIGINS = env('CORS_ALLOW_ALL', default=False, cast=bool)
_cors_origins = env('CORS_ALLOWED_ORIGINS', default='')
if _cors_origins and not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(',')]

# Fichiers media — monter un Railway Volume sur /app/media
MEDIA_ROOT = '/app/media'

# ── CACHE (Redis sur Railway) ────────────────────────────────────
_REDIS_URL = os.environ.get('REDIS_URL', '').strip()
if _REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _REDIS_URL,
            'OPTIONS': {
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
            },
        }
    }

# ── SENTRY ───────────────────────────────────────────────────────
_SENTRY_DSN = env('SENTRY_DSN', default='')
if _SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        integrations=[DjangoIntegration(auto_enabling_integrations=False)],
        traces_sample_rate=0.05,
        send_default_pii=False,
        environment='production',
    )
