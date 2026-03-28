from .panier_views   import (
    panier_resume, panier_ajouter, panier_modifier,
    panier_retirer, panier_vider,
)
from .commande_views import commander

__all__ = [
    'panier_resume', 'panier_ajouter', 'panier_modifier',
    'panier_retirer', 'panier_vider',
    'commander',
]
