from django.db import models
from django.utils.translation import gettext_lazy as _


class CommandeDetail(models.Model):
    commande       = models.ForeignKey('orders.Commande', on_delete=models.CASCADE, related_name='details')
    produit        = models.ForeignKey('catalog.Produit', on_delete=models.PROTECT, related_name='lignes_commande')
    lot            = models.ForeignKey('stock.Lot', on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_commande')
    prix_unitaire  = models.DecimalField(max_digits=10, decimal_places=2)
    quantite       = models.PositiveIntegerField()
    unite_vente    = models.CharField(max_length=20)
    sous_total     = models.DecimalField(max_digits=12, decimal_places=2)
    est_disponible = models.BooleanField(default=True)
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = _('Detail commande')
        verbose_name_plural = _('Details commande')

    def __str__(self):
        return f"{self.commande.numero_commande} — {self.produit.nom} x{self.quantite}"

    def save(self, *args, **kwargs):
        self.sous_total = self.prix_unitaire * self.quantite
        super().save(*args, **kwargs)


class HistoriqueStatutCommande(models.Model):
    commande     = models.ForeignKey('orders.Commande', on_delete=models.CASCADE, related_name='historique_statuts')
    statut_avant = models.CharField(max_length=20)
    statut_apres = models.CharField(max_length=20)
    commentaire  = models.TextField(blank=True)
    effectue_par = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = _('Historique statut')
        verbose_name_plural = _('Historiques statuts')
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.commande.numero_commande} | {self.statut_avant} -> {self.statut_apres} | {self.created_at.strftime('%d/%m/%Y %H:%M')}"
