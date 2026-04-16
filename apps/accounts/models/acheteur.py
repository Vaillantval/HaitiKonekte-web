from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Acheteur(models.Model):
    class TypeAcheteur(models.TextChoices):
        PARTICULIER = 'particulier', _('Particulier')
        GROSSISTE   = 'grossiste',   _('Grossiste')
        DETAILLANT  = 'detaillant',  _('Detaillant')
        COOPERATIVE = 'cooperative', _('Cooperative')
        INSTITUTION = 'institution', _('Institution / ONG')
        RESTAURANT  = 'restaurant',  _('Restaurant / Hotel')

    user             = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil_acheteur')
    type_acheteur    = models.CharField(max_length=20, choices=TypeAcheteur.choices, default=TypeAcheteur.PARTICULIER)
    nom_organisation = models.CharField(max_length=200, blank=True)
    adresse          = models.TextField(blank=True)
    ville            = models.CharField(max_length=100, blank=True)
    departement      = models.CharField(max_length=100, blank=True)
    categories_preferees = models.ManyToManyField('catalog.Categorie', blank=True, related_name='acheteurs_interesses')
    total_commandes  = models.PositiveIntegerField(default=0)
    total_depense    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = _('Acheteur')
        verbose_name_plural = _('Acheteurs')
        ordering            = ['-created_at']

    def __str__(self):
        label = self.nom_organisation or self.user.get_full_name()
        return f"{label} ({self.get_type_acheteur_display()})"
