from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Panier(models.Model):
    """
    Panier persistant en base de données.
    Un panier par utilisateur connecté.
    """
    user       = models.OneToOneField(
                   settings.AUTH_USER_MODEL,
                   on_delete=models.CASCADE,
                   related_name='panier'
                 )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = _('Panier')
        verbose_name_plural = _('Paniers')

    def __str__(self):
        return f"Panier de {self.user.get_full_name()}"

    @property
    def nb_articles(self):
        """Nombre total d'articles (somme des quantités)."""
        return sum(item.quantite for item in self.items.all())

    @property
    def nb_items(self):
        """Nombre de lignes distinctes."""
        return self.items.count()

    @property
    def total(self):
        """Total du panier en HTG."""
        return sum(item.sous_total for item in self.items.all())

    @property
    def producteurs(self):
        """Liste des producteurs distincts dans le panier."""
        return list(
            self.items.select_related('produit__producteur__user')
            .values(
                'produit__producteur__id',
                'produit__producteur__user__first_name',
                'produit__producteur__user__last_name',
            )
            .distinct()
        )


class LignePanier(models.Model):
    """
    Ligne d'un panier — un produit avec sa quantité.
    """
    panier     = models.ForeignKey(
                   Panier,
                   on_delete=models.CASCADE,
                   related_name='items'
                 )
    produit    = models.ForeignKey(
                   'catalog.Produit',
                   on_delete=models.CASCADE,
                   related_name='lignes_panier'
                 )
    quantite   = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = _('Ligne panier')
        verbose_name_plural = _('Lignes panier')
        unique_together     = ('panier', 'produit')

    def __str__(self):
        return f"{self.produit.nom} x{self.quantite}"

    @property
    def sous_total(self):
        return self.produit.prix_unitaire * self.quantite
