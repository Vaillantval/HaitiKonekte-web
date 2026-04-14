from .auth_views import (
    register, login, logout, me, change_password, fcm_token,
    acheteur_commandes, acheteur_commande_detail,
    acheteur_vouchers,
)
from .adresse_views    import adresses_list, adresse_detail, adresse_set_default
from .producteur_views import (
    producteur_stats,
    producteur_profil,
    producteur_commandes,
    producteur_commande_detail,
    producteur_commande_statut,
)

__all__ = [
    'register', 'login', 'logout', 'me', 'change_password', 'fcm_token',
    'acheteur_commandes', 'acheteur_commande_detail', 'acheteur_vouchers',
    'adresses_list', 'adresse_detail', 'adresse_set_default',
    'producteur_stats', 'producteur_profil',
    'producteur_commandes', 'producteur_commande_detail',
    'producteur_commande_statut',
]
