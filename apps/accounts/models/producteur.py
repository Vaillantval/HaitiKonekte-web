from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Departement(models.TextChoices):
    OUEST      = 'ouest',      _('Ouest')
    SUD_EST    = 'sud_est',    _('Sud-Est')
    NORD       = 'nord',       _('Nord')
    NORD_EST   = 'nord_est',   _('Nord-Est')
    ARTIBONITE = 'artibonite', _('Artibonite')
    CENTRE     = 'centre',     _('Centre')
    SUD        = 'sud',        _('Sud')
    GRAND_ANSE = 'grand_anse', _('Grand-Anse')
    NORD_OUEST = 'nord_ouest', _('Nord-Ouest')
    NIPPES     = 'nippes',     _('Nippes')


class Producteur(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente de validation')
        ACTIF      = 'actif',      _('Actif')
        SUSPENDU   = 'suspendu',   _('Suspendu')
        INACTIF    = 'inactif',    _('Inactif')

    user             = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil_producteur')
    departement      = models.CharField(max_length=20, choices=Departement.choices)
    commune          = models.CharField(max_length=100)
    localite         = models.CharField(max_length=100, blank=True)
    adresse_complete = models.TextField(blank=True)
    superficie_ha    = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    description      = models.TextField(blank=True)
    code_producteur  = models.CharField(max_length=20, unique=True, blank=True)
    num_identification = models.CharField(max_length=50, blank=True)
    photo_identite   = models.ImageField(upload_to='producteurs/identites/', null=True, blank=True)
    statut           = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    note_admin       = models.TextField(blank=True)
    valide_par       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='producteurs_valides')
    date_validation  = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = _('Producteur')
        verbose_name_plural = _('Producteurs')
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.commune} ({self.get_departement_display()})"

    def save(self, *args, **kwargs):
        if not self.code_producteur:
            from django.utils import timezone
            annee = timezone.now().year
            last  = Producteur.objects.filter(code_producteur__startswith=f'PROD-{annee}-').count()
            self.code_producteur = f'PROD-{annee}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    @property
    def nb_produits_actifs(self):
        return self.produits.filter(is_active=True).count()

    @property
    def nb_commandes_total(self):
        return self.commandes_recues.count()
