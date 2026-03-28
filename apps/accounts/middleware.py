"""
JWTCookieAuthMiddleware
=======================
Lit le cookie `mp_jwt` (access token) et authentifie `request.user`
pour les vues Django normales (templates) qui n'utilisent pas DRF.

Cela permet au CartService de détecter l'utilisateur connecté via JWT
et d'utiliser le backend DB (Panier/LignePanier) plutôt que la session.
"""
from django.utils.functional import SimpleLazyObject


def _get_user_from_jwt_cookie(request):
    token_str = request.COOKIES.get('mp_jwt', '').strip()
    if not token_str:
        return None
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from apps.accounts.models import CustomUser
        token = AccessToken(token_str)
        return CustomUser.objects.get(pk=token['user_id'], is_active=True)
    except Exception:
        return None


class JWTCookieAuthMiddleware:
    """
    Middleware léger : si `request.user` est anonyme ET que le cookie
    `mp_jwt` est présent et valide, on substitue un vrai User.
    Positionner APRÈS AuthenticationMiddleware dans MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_anonymous:
            user = _get_user_from_jwt_cookie(request)
            if user is not None:
                request.user = user
        return self.get_response(request)
