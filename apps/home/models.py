from django.db import models


class SiteConfig(models.Model):
    """Configuration générale du site."""
    nom_site         = models.CharField(max_length=100, default='Makèt Peyizan')
    slogan           = models.TextField(blank=True)
    email_contact    = models.EmailField(blank=True)
    telephone        = models.CharField(max_length=20, blank=True)
    adresse          = models.TextField(blank=True)
    facebook_url     = models.URLField(blank=True)
    instagram_url    = models.URLField(blank=True)
    whatsapp_numero  = models.CharField(max_length=20, blank=True)
    is_active        = models.BooleanField(default=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Configuration site'
        verbose_name_plural = 'Configurations site'

    def __str__(self):
        return self.nom_site

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class FAQCategorie(models.Model):
    """Catégorie de questions fréquentes."""
    titre     = models.CharField(max_length=100)
    ordre     = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Catégorie FAQ'
        verbose_name_plural = 'Catégories FAQ'
        ordering            = ['ordre', 'titre']

    def __str__(self):
        return self.titre


class FAQItem(models.Model):
    """Question/réponse fréquente."""
    categorie = models.ForeignKey(
                  FAQCategorie,
                  on_delete=models.CASCADE,
                  related_name='items'
                )
    question  = models.CharField(max_length=300)
    reponse   = models.TextField()
    ordre     = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Item FAQ'
        verbose_name_plural = 'Items FAQ'
        ordering            = ['ordre']

    def __str__(self):
        return self.question


class ContactMessage(models.Model):
    """Message envoyé via le formulaire de contact."""
    class Statut(models.TextChoices):
        NOUVEAU  = 'nouveau',  'Nouveau'
        LU       = 'lu',       'Lu'
        REPONDU  = 'repondu',  'Répondu'
        ARCHIVE  = 'archive',  'Archivé'

    nom        = models.CharField(max_length=100)
    email      = models.EmailField()
    sujet      = models.CharField(max_length=200, blank=True)
    message    = models.TextField()
    statut     = models.CharField(
                   max_length=20,
                   choices=Statut.choices,
                   default=Statut.NOUVEAU
                 )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.nom} — {self.sujet}"
