# PROMPT CLAUDE CODE — Makèt Peyizan
# API REST — Partie 4 : API Superadmin Complète

---

## CONTEXTE

Tu travailles sur **Makèt Peyizan** (marketplace agricole haïtienne).
Les Parties 1, 2 et 3 sont déjà implémentées et fonctionnelles.

Tu vas maintenant implémenter **l'API Superadmin complète** accessible
uniquement aux utilisateurs avec `is_staff=True`, `is_superuser=True`
ou `role='superadmin'`.

**Format de réponse uniforme :**
- Succès : `{ "success": true, "data": {...} }`
- Erreur  : `{ "success": false, "error": "message" }`

**Permission requise sur tous les endpoints :** `IsSuperAdmin`
(déjà créée dans `apps/accounts/permissions.py`)

---

## FICHIERS À CRÉER

```
apps/api_admin/
├── __init__.py
├── apps.py
├── urls.py
├── serializers/
│   ├── __init__.py
│   ├── stats_serializers.py
│   ├── user_serializers.py
│   ├── producteur_serializers.py
│   ├── commande_serializers.py
│   ├── catalogue_serializers.py
│   ├── stock_serializers.py
│   ├── collecte_serializers.py
│   └── config_serializers.py
└── views/
    ├── __init__.py
    ├── stats_views.py
    ├── user_views.py
    ├── producteur_views.py
    ├── commande_views.py
    ├── catalogue_views.py
    ├── stock_views.py
    ├── collecte_views.py
    └── config_views.py

apps/home/
├── models.py    ← nouveaux modèles FAQ + Contact + SiteConfig
```

---

## ÉTAPE 1 — App api_admin

### `apps/api_admin/apps.py`
```python
from django.apps import AppConfig

class ApiAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'apps.api_admin'
    verbose_name       = 'API Admin'
```

### `apps/api_admin/__init__.py`
```python
default_app_config = 'apps.api_admin.apps.ApiAdminConfig'
```

Ajouter dans `config/settings/base.py` → `LOCAL_APPS` :
```python
'apps.api_admin',
```

---

## ÉTAPE 2 — Modèles Site Config, FAQ, Contact

### `apps/home/models.py`

```python
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
    titre   = models.CharField(max_length=100)
    ordre   = models.PositiveSmallIntegerField(default=0)
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
        NOUVEAU    = 'nouveau',    'Nouveau'
        LU         = 'lu',         'Lu'
        REPONDU    = 'repondu',    'Répondu'
        ARCHIVE    = 'archive',    'Archivé'

    nom       = models.CharField(max_length=100)
    email     = models.EmailField()
    sujet     = models.CharField(max_length=200, blank=True)
    message   = models.TextField()
    statut    = models.CharField(
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
```

Créer la migration :
```bash
python manage.py makemigrations home --settings=config.settings.development
python manage.py migrate --settings=config.settings.development
```

---

## ÉTAPE 3 — Serializers Stats

### `apps/api_admin/serializers/stats_serializers.py`

```python
from rest_framework import serializers


class GlobalStatsSerializer(serializers.Serializer):
    """Statistiques globales pour le dashboard admin."""
    # Utilisateurs
    total_users           = serializers.IntegerField()
    total_producteurs     = serializers.IntegerField()
    producteurs_actifs    = serializers.IntegerField()
    producteurs_attente   = serializers.IntegerField()
    total_acheteurs       = serializers.IntegerField()
    nouveaux_users_30j    = serializers.IntegerField()

    # Commandes
    total_commandes       = serializers.IntegerField()
    commandes_en_attente  = serializers.IntegerField()
    commandes_livrees     = serializers.IntegerField()
    commandes_annulees    = serializers.IntegerField()
    commandes_litige      = serializers.IntegerField()
    commandes_mois        = serializers.IntegerField()

    # Revenus
    revenu_total          = serializers.DecimalField(max_digits=14, decimal_places=2)
    revenu_mois           = serializers.DecimalField(max_digits=14, decimal_places=2)
    revenu_7j             = serializers.DecimalField(max_digits=14, decimal_places=2)

    # Paiements
    paiements_a_verifier  = serializers.IntegerField()
    montant_a_verifier    = serializers.DecimalField(max_digits=14, decimal_places=2)

    # Produits & Stock
    total_produits        = serializers.IntegerField()
    produits_epuises      = serializers.IntegerField()
    alertes_stock         = serializers.IntegerField()

    # Collectes
    collectes_planifiees  = serializers.IntegerField()
    collectes_en_cours    = serializers.IntegerField()
    collectes_en_retard   = serializers.IntegerField()

    # Vouchers
    vouchers_actifs       = serializers.IntegerField()
```

---

## ÉTAPE 4 — Vues Stats

### `apps/api_admin/views/stats_views.py`

```python
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.accounts.models import CustomUser, Producteur, Acheteur
from apps.catalog.models import Produit
from apps.orders.models import Commande
from apps.payments.models import Paiement, Voucher
from apps.stock.models import AlerteStock
from apps.collectes.models import Collecte
from apps.api_admin.serializers.stats_serializers import GlobalStatsSerializer
from datetime import timedelta


# ── GET /api/admin/stats/ ────────────────────────────────────────
@extend_schema(tags=['Admin — Stats'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def global_stats(request):
    """Statistiques globales de la plateforme."""
    aujourd_hui     = timezone.now().date()
    debut_mois      = aujourd_hui.replace(day=1)
    il_y_a_7j       = aujourd_hui - timedelta(days=7)
    il_y_a_30j      = aujourd_hui - timedelta(days=30)

    commandes_actives = Commande.objects.filter(
        statut__in=['confirmee', 'en_preparation', 'prete', 'en_collecte', 'livree']
    )

    revenu_total = commandes_actives.filter(
        statut_paiement='paye'
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    revenu_mois = commandes_actives.filter(
        statut_paiement='paye',
        created_at__date__gte=debut_mois
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    revenu_7j = commandes_actives.filter(
        statut_paiement='paye',
        created_at__date__gte=il_y_a_7j
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    montant_a_verifier = Paiement.objects.filter(
        statut=Paiement.Statut.SOUMIS
    ).aggregate(t=Sum('montant'))['t'] or Decimal('0')

    collectes_en_retard = Collecte.objects.filter(
        statut='planifiee',
        date_prevue__lt=aujourd_hui
    ).count() if hasattr(Collecte, 'date_prevue') else Collecte.objects.filter(
        statut='planifiee',
        date_planifiee__lt=aujourd_hui
    ).count()

    stats = {
        'total_users':           CustomUser.objects.count(),
        'total_producteurs':     Producteur.objects.count(),
        'producteurs_actifs':    Producteur.objects.filter(statut='actif').count(),
        'producteurs_attente':   Producteur.objects.filter(statut='en_attente').count(),
        'total_acheteurs':       Acheteur.objects.count(),
        'nouveaux_users_30j':    CustomUser.objects.filter(
                                   created_at__date__gte=il_y_a_30j
                                 ).count(),
        'total_commandes':       Commande.objects.count(),
        'commandes_en_attente':  Commande.objects.filter(statut='en_attente').count(),
        'commandes_livrees':     Commande.objects.filter(statut='livree').count(),
        'commandes_annulees':    Commande.objects.filter(statut='annulee').count(),
        'commandes_litige':      Commande.objects.filter(statut='litige').count(),
        'commandes_mois':        Commande.objects.filter(
                                   created_at__date__gte=debut_mois
                                 ).count(),
        'revenu_total':          revenu_total,
        'revenu_mois':           revenu_mois,
        'revenu_7j':             revenu_7j,
        'paiements_a_verifier':  Paiement.objects.filter(
                                   statut=Paiement.Statut.SOUMIS
                                 ).count(),
        'montant_a_verifier':    montant_a_verifier,
        'total_produits':        Produit.objects.filter(is_active=True).count(),
        'produits_epuises':      Produit.objects.filter(statut='epuise').count(),
        'alertes_stock':         AlerteStock.objects.filter(
                                   statut__in=['nouvelle', 'vue']
                                 ).count(),
        'collectes_planifiees':  Collecte.objects.filter(
                                   statut='planifiee'
                                 ).count(),
        'collectes_en_cours':    Collecte.objects.filter(
                                   statut='en_cours'
                                 ).count(),
        'collectes_en_retard':   collectes_en_retard,
        'vouchers_actifs':       Voucher.objects.filter(
                                   statut='actif'
                                 ).count(),
    }

    serializer = GlobalStatsSerializer(stats)
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/admin/options/ ─────────────────────────────────────
@extend_schema(tags=['Admin — Stats'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def admin_options(request):
    """
    Listes d'options pour les selects/dropdowns du dashboard admin.
    ?type=categories|producteurs|produits|zones|points|collecteurs
    """
    type_option = request.query_params.get('type', '')

    if type_option == 'categories':
        from apps.catalog.models import Categorie
        data = list(
            Categorie.objects.filter(is_active=True)
            .values('id', 'nom', 'slug')
        )

    elif type_option == 'producteurs':
        data = [
            {
                'id':   p.pk,
                'nom':  p.user.get_full_name(),
                'code': p.code_producteur,
            }
            for p in Producteur.objects.filter(
                statut='actif'
            ).select_related('user')
        ]

    elif type_option == 'produits':
        data = list(
            Produit.objects.filter(is_active=True)
            .values('id', 'nom', 'slug', 'prix_unitaire')
        )

    elif type_option == 'zones':
        from apps.collectes.models import ZoneCollecte
        data = list(
            ZoneCollecte.objects.filter(est_active=True)
            .values('id', 'nom', 'departement')
        )

    elif type_option == 'points':
        from apps.collectes.models import PointCollecte
        data = list(
            PointCollecte.objects.filter(statut='actif')
            .values('id', 'nom', 'commune', 'departement')
        )

    elif type_option == 'collecteurs':
        data = [
            {
                'id':  u.pk,
                'nom': u.get_full_name(),
            }
            for u in CustomUser.objects.filter(
                role='collecteur', is_active=True
            )
        ]

    else:
        return Response(
            {
                'success': False,
                'error': (
                    "Paramètre 'type' requis. "
                    "Valeurs : categories, producteurs, produits, "
                    "zones, points, collecteurs"
                )
            },
            status=400
        )

    return Response({'success': True, 'data': data})
```

---

## ÉTAPE 5 — Vues Utilisateurs Admin

### `apps/api_admin/views/user_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.accounts.models import CustomUser
from apps.accounts.serializers import RegisterSerializer, UserProfileSerializer


# ── GET /api/admin/users/ ────────────────────────────────────────
@extend_schema(tags=['Admin — Utilisateurs'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def users_list(request):
    """Liste des utilisateurs avec filtres."""
    search    = request.query_params.get('search', '')
    role      = request.query_params.get('role', '')
    is_active = request.query_params.get('is_active', '')

    qs = CustomUser.objects.order_by('-created_at')

    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)  |
            Q(email__icontains=search)      |
            Q(username__icontains=search)   |
            Q(telephone__icontains=search)
        )
    if role:
        qs = qs.filter(role=role)
    if is_active:
        qs = qs.filter(is_active=(is_active.lower() == 'true'))

    data = UserProfileSerializer(
        qs, many=True, context={'request': request}
    ).data
    return Response({'success': True, 'data': data})


# ── POST /api/admin/users/create/ ───────────────────────────────
@extend_schema(tags=['Admin — Utilisateurs'])
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def user_create(request):
    """Créer un utilisateur."""
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    user = serializer.save()
    return Response(
        {
            'success': True,
            'data': UserProfileSerializer(
                user, context={'request': request}
            ).data
        },
        status=status.HTTP_201_CREATED
    )


# ── GET/PATCH /api/admin/users/<id>/detail/ ─────────────────────
@extend_schema(tags=['Admin — Utilisateurs'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def user_detail(request, pk):
    """Détail ou mise à jour d'un utilisateur."""
    user = get_object_or_404(CustomUser, pk=pk)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': UserProfileSerializer(
                user, context={'request': request}
            ).data
        })

    serializer = UserProfileSerializer(
        user, data=request.data,
        partial=True,
        context={'request': request}
    )
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer.save()
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/admin/users/<id>/toggle/ ─────────────────────────
@extend_schema(tags=['Admin — Utilisateurs'])
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def user_toggle(request, pk):
    """Activer ou désactiver un utilisateur."""
    user           = get_object_or_404(CustomUser, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return Response({
        'success': True,
        'data': {
            'id':        user.pk,
            'is_active': user.is_active,
            'message':   f"Compte {'activé' if user.is_active else 'désactivé'}."
        }
    })
```

---

## ÉTAPE 6 — Vues Producteurs Admin

### `apps/api_admin/views/producteur_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.accounts.models import Producteur, CustomUser
from apps.accounts.serializers import ProducteurProfilSerializer
from apps.accounts.serializers.auth_serializers import RegisterSerializer


# ── GET /api/admin/producteurs/ ─────────────────────────────────
@extend_schema(tags=['Admin — Producteurs'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def producteurs_list(request):
    """Liste des producteurs avec filtres."""
    statut = request.query_params.get('statut', '')
    search = request.query_params.get('search', '')

    qs = Producteur.objects.select_related('user').order_by('-created_at')

    if statut:
        qs = qs.filter(statut=statut)
    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)  |
            Q(code_producteur__icontains=search)  |
            Q(commune__icontains=search)
        )

    data = ProducteurProfilSerializer(
        qs, many=True, context={'request': request}
    ).data
    return Response({'success': True, 'data': data})


# ── POST /api/admin/producteurs/create/ ─────────────────────────
@extend_schema(tags=['Admin — Producteurs'])
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def producteur_create(request):
    """Créer un producteur directement validé."""
    data = request.data.copy()
    data['role'] = 'producteur'

    serializer = RegisterSerializer(data=data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    user       = serializer.save()
    producteur = user.profil_producteur
    # L'admin crée directement en statut actif
    producteur.statut         = 'actif'
    producteur.valide_par     = request.user
    producteur.date_validation = timezone.now()
    producteur.save()

    return Response(
        {
            'success': True,
            'data': ProducteurProfilSerializer(
                producteur, context={'request': request}
            ).data
        },
        status=status.HTTP_201_CREATED
    )


# ── GET/PATCH /api/admin/producteurs/<id>/detail/ ───────────────
@extend_schema(tags=['Admin — Producteurs'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def producteur_detail(request, pk):
    """Détail ou mise à jour d'un producteur."""
    producteur = get_object_or_404(Producteur, pk=pk)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': ProducteurProfilSerializer(
                producteur, context={'request': request}
            ).data
        })

    serializer = ProducteurProfilSerializer(
        producteur, data=request.data,
        partial=True,
        context={'request': request}
    )
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer.save()
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/admin/producteurs/<id>/statut/ ───────────────────
@extend_schema(tags=['Admin — Producteurs'])
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def producteur_statut(request, pk):
    """
    Changer le statut d'un producteur.
    Body : { "statut": "actif" | "suspendu" | "en_attente" | "inactif",
             "note": "..." }
    """
    producteur  = get_object_or_404(Producteur, pk=pk)
    nouveau_statut = request.data.get('statut')
    note           = request.data.get('note', '')

    STATUTS_VALIDES = ['actif', 'suspendu', 'en_attente', 'inactif']
    if nouveau_statut not in STATUTS_VALIDES:
        return Response(
            {
                'success': False,
                'error': f"Statut invalide. Valeurs : {STATUTS_VALIDES}"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    ancien_statut      = producteur.statut
    producteur.statut  = nouveau_statut

    if note:
        producteur.note_admin = note

    if nouveau_statut == 'actif' and ancien_statut != 'actif':
        producteur.valide_par      = request.user
        producteur.date_validation = timezone.now()

    producteur.save()

    return Response({
        'success': True,
        'data': {
            'id':             producteur.pk,
            'code_producteur': producteur.code_producteur,
            'statut':         producteur.statut,
            'message':        f"Statut mis à jour : {nouveau_statut}."
        }
    })
```

---

## ÉTAPE 7 — Vues Commandes Admin

### `apps/api_admin/views/commande_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.orders.models import Commande
from apps.orders.services.commande_service import CommandeService
from apps.accounts.serializers.producteur_serializers import CommandeProducteurSerializer


# ── GET /api/admin/commandes/ ────────────────────────────────────
@extend_schema(tags=['Admin — Commandes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def commandes_list(request):
    """Toutes les commandes avec filtres."""
    statut = request.query_params.get('statut', '')
    search = request.query_params.get('search', '')

    qs = Commande.objects.select_related(
        'acheteur__user',
        'producteur__user'
    ).prefetch_related('details__produit').order_by('-created_at')

    if statut:
        qs = qs.filter(statut=statut)
    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(numero_commande__icontains=search)        |
            Q(acheteur__user__first_name__icontains=search) |
            Q(acheteur__user__last_name__icontains=search)  |
            Q(producteur__user__first_name__icontains=search)
        )

    serializer = CommandeProducteurSerializer(qs, many=True)
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/admin/commandes/<numero>/ ──────────────────────────
@extend_schema(tags=['Admin — Commandes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def commande_detail(request, numero):
    """Détail complet d'une commande."""
    commande   = get_object_or_404(Commande, numero_commande=numero)
    serializer = CommandeProducteurSerializer(commande)
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/admin/commandes/<numero>/statut/ ─────────────────
@extend_schema(tags=['Admin — Commandes'])
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def commande_statut(request, numero):
    """
    Changer le statut d'une commande.
    Body : { "statut": "confirmee|en_preparation|prete|en_collecte|livree|annulee|litige",
             "commentaire": "..." }
    """
    commande    = get_object_or_404(Commande, numero_commande=numero)
    nouveau     = request.data.get('statut')
    commentaire = request.data.get('commentaire', '')

    STATUTS = [
        'confirmee', 'en_preparation', 'prete',
        'en_collecte', 'livree', 'annulee', 'litige'
    ]
    if nouveau not in STATUTS:
        return Response(
            {'success': False, 'error': f"Statut invalide. Valeurs : {STATUTS}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if nouveau == 'annulee':
            CommandeService.annuler_commande(
                commande, request.user, commentaire
            )
        else:
            CommandeService.changer_statut(
                commande, nouveau,
                effectue_par=request.user,
                commentaire=commentaire
            )
    except ValueError as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        'success': True,
        'data': {
            'numero_commande': commande.numero_commande,
            'statut':          commande.statut,
            'statut_label':    commande.get_statut_display(),
        }
    })
```

---

## ÉTAPE 8 — Vues Paiements Admin

### `apps/api_admin/views/paiement_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.payments.models import Paiement
from apps.payments.serializers import PaiementSerializer
from apps.payments.services.paiement_service import PaiementService


# ── GET /api/admin/paiements/ ────────────────────────────────────
@extend_schema(tags=['Admin — Paiements'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def paiements_list(request):
    """Tous les paiements avec filtre par statut."""
    statut = request.query_params.get('statut', '')

    qs = Paiement.objects.select_related(
        'commande__acheteur__user'
    ).order_by('-created_at')

    if statut:
        qs = qs.filter(statut=statut)

    serializer = PaiementSerializer(qs, many=True)
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/admin/paiements/<id>/statut/ ─────────────────────
@extend_schema(tags=['Admin — Paiements'])
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def paiement_statut(request, pk):
    """
    Confirmer ou rejeter un paiement.
    Body : { "action": "confirmer" | "rejeter", "note": "..." }
    """
    paiement = get_object_or_404(Paiement, pk=pk)
    action   = request.data.get('action')
    note     = request.data.get('note', '')

    if action not in ['confirmer', 'rejeter']:
        return Response(
            {'success': False, 'error': "Action : 'confirmer' ou 'rejeter'."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if action == 'confirmer':
        paiement = PaiementService.confirmer_paiement(
            paiement=paiement,
            verifie_par=request.user,
            note_verification=note,
        )
    else:
        paiement = PaiementService.rejeter_paiement(
            paiement=paiement,
            verifie_par=request.user,
            motif=note,
        )

    return Response({
        'success': True,
        'data': PaiementSerializer(paiement).data
    })
```

---

## ÉTAPE 9 — Vues Catalogue Admin

### `apps/api_admin/views/catalogue_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.catalog.models import Produit, Categorie
from apps.catalog.serializers import (
    ProduitListSerializer,
    ProduitDetailSerializer,
    ProduitCreateUpdateSerializer,
    CategorieSerializer,
)
from apps.accounts.models import Producteur


# ── GET /api/admin/catalogue/ ────────────────────────────────────
@extend_schema(tags=['Admin — Catalogue'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def catalogue_list(request):
    """Tous les produits (tous statuts) avec filtres."""
    search       = request.query_params.get('search', '')
    statut       = request.query_params.get('statut', '')
    producteur_id = request.query_params.get('producteur_id', '')

    qs = Produit.objects.select_related(
        'categorie', 'producteur__user'
    ).order_by('-created_at')

    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(nom__icontains=search) |
            Q(variete__icontains=search) |
            Q(producteur__user__first_name__icontains=search)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if producteur_id:
        qs = qs.filter(producteur__pk=producteur_id)

    serializer = ProduitListSerializer(
        qs, many=True, context={'request': request}
    )
    return Response({'success': True, 'data': serializer.data})


# ── POST /api/admin/catalogue/create/ ───────────────────────────
@extend_schema(tags=['Admin — Catalogue'])
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def catalogue_create(request):
    """Créer un produit (multipart/form-data)."""
    producteur_id = request.data.get('producteur_id')
    producteur    = get_object_or_404(Producteur, pk=producteur_id)

    serializer = ProduitCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    produit = serializer.save(
        producteur=producteur,
        statut='actif',
        is_active=True
    )
    return Response(
        {
            'success': True,
            'data': ProduitDetailSerializer(
                produit, context={'request': request}
            ).data
        },
        status=status.HTTP_201_CREATED
    )


# ── GET/PATCH /api/admin/catalogue/<id>/detail/ ─────────────────
@extend_schema(tags=['Admin — Catalogue'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def catalogue_detail(request, pk):
    """Détail ou mise à jour d'un produit."""
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': ProduitDetailSerializer(
                produit, context={'request': request}
            ).data
        })

    serializer = ProduitCreateUpdateSerializer(
        produit, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer.save()
    return Response({
        'success': True,
        'data': ProduitDetailSerializer(
            produit, context={'request': request}
        ).data
    })


# ── PATCH /api/admin/catalogue/<id>/statut/ ─────────────────────
@extend_schema(tags=['Admin — Catalogue'])
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def catalogue_statut(request, pk):
    """Changer le statut d'un produit."""
    produit        = get_object_or_404(Produit, pk=pk)
    nouveau_statut = request.data.get('statut')

    STATUTS = ['brouillon', 'en_attente', 'actif', 'epuise', 'inactif']
    if nouveau_statut not in STATUTS:
        return Response(
            {'success': False, 'error': f"Statut invalide : {STATUTS}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    produit.statut    = nouveau_statut
    produit.is_active = (nouveau_statut == 'actif')
    produit.save(update_fields=['statut', 'is_active'])

    return Response({
        'success': True,
        'data': {
            'id':     produit.pk,
            'statut': produit.statut,
        }
    })


# ── PATCH /api/admin/catalogue/<id>/toggle/ ─────────────────────
@extend_schema(tags=['Admin — Catalogue'])
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def catalogue_toggle(request, pk):
    """
    Basculer is_active ou is_featured d'un produit.
    Body : { "champ": "is_active" | "is_featured" }
    """
    produit = get_object_or_404(Produit, pk=pk)
    champ   = request.data.get('champ')

    if champ not in ['is_active', 'is_featured']:
        return Response(
            {'success': False, 'error': "Champ : 'is_active' ou 'is_featured'."},
            status=status.HTTP_400_BAD_REQUEST
        )

    nouvelle_val = not getattr(produit, champ)
    setattr(produit, champ, nouvelle_val)
    produit.save(update_fields=[champ])

    return Response({
        'success': True,
        'data': {
            'id':     produit.pk,
            champ:    nouvelle_val,
        }
    })


# ── GET/POST /api/admin/categories/ ─────────────────────────────
@extend_schema(tags=['Admin — Catalogue'])
@api_view(['GET', 'POST'])
@permission_classes([IsSuperAdmin])
def categories_admin(request):
    if request.method == 'GET':
        cats = Categorie.objects.all().order_by('ordre', 'nom')
        return Response({
            'success': True,
            'data': CategorieSerializer(cats, many=True).data
        })

    serializer = CategorieSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    cat = serializer.save()
    return Response(
        {'success': True, 'data': CategorieSerializer(cat).data},
        status=status.HTTP_201_CREATED
    )


# ── GET/PATCH /api/admin/categories/<id>/ ───────────────────────
@extend_schema(tags=['Admin — Catalogue'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def categorie_detail(request, pk):
    cat = get_object_or_404(Categorie, pk=pk)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': CategorieSerializer(cat).data
        })

    serializer = CategorieSerializer(cat, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer.save()
    return Response({'success': True, 'data': serializer.data})
```

---

## ÉTAPE 10 — Vues Stocks Admin

### `apps/api_admin/views/stock_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.stock.models import Lot, MouvementStock, AlerteStock
from apps.stock.services.stock_service import StockService


def _lot_data(lot):
    return {
        'id':               lot.pk,
        'numero_lot':       lot.numero_lot,
        'produit':          lot.produit.nom,
        'producteur':       lot.produit.producteur.user.get_full_name(),
        'quantite_initiale': lot.quantite_initiale,
        'quantite_actuelle': lot.quantite_actuelle,
        'quantite_vendue':  lot.quantite_vendue,
        'taux_ecoulement':  lot.taux_ecoulement,
        'statut':           lot.statut,
        'date_recolte':     str(lot.date_recolte) if lot.date_recolte else None,
        'lieu_stockage':    lot.lieu_stockage,
        'created_at':       lot.created_at.isoformat(),
    }


# ── GET /api/admin/stocks/lots/ ──────────────────────────────────
@extend_schema(tags=['Admin — Stocks'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def lots_list(request):
    """Liste des lots avec filtres."""
    search       = request.query_params.get('search', '')
    statut       = request.query_params.get('statut', '')
    producteur_id = request.query_params.get('producteur_id', '')

    qs = Lot.objects.select_related(
        'produit__producteur__user'
    ).order_by('-created_at')

    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(numero_lot__icontains=search) |
            Q(produit__nom__icontains=search)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if producteur_id:
        qs = qs.filter(produit__producteur__pk=producteur_id)

    return Response({
        'success': True,
        'data': [_lot_data(l) for l in qs]
    })


# ── POST /api/admin/stocks/lots/create/ ─────────────────────────
@extend_schema(tags=['Admin — Stocks'])
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def lot_create(request):
    """Créer un nouveau lot de stock."""
    from apps.catalog.models import Produit
    produit_id = request.data.get('produit_id')
    produit    = get_object_or_404(Produit, pk=produit_id)

    quantite = int(request.data.get('quantite', 0))
    if quantite <= 0:
        return Response(
            {'success': False, 'error': "La quantité doit être > 0."},
            status=status.HTTP_400_BAD_REQUEST
        )

    lot = Lot.objects.create(
        produit=produit,
        quantite_initiale=quantite,
        quantite_actuelle=quantite,
        date_recolte=request.data.get('date_recolte'),
        lieu_stockage=request.data.get('lieu_stockage', ''),
        notes=request.data.get('notes', ''),
        cree_par=request.user,
        statut='disponible',
    )

    return Response(
        {'success': True, 'data': _lot_data(lot)},
        status=status.HTTP_201_CREATED
    )


# ── GET/PATCH /api/admin/stocks/lots/<id>/ ──────────────────────
@extend_schema(tags=['Admin — Stocks'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def lot_detail(request, pk):
    """Détail ou ajustement d'un lot."""
    lot = get_object_or_404(Lot, pk=pk)

    if request.method == 'GET':
        return Response({'success': True, 'data': _lot_data(lot)})

    # PATCH — ajustement du stock
    nouvelle_quantite = request.data.get('quantite_actuelle')
    motif             = request.data.get('motif', 'Ajustement admin')

    if nouvelle_quantite is not None:
        try:
            StockService.ajustement_stock(
                lot=lot,
                nouvelle_quantite=int(nouvelle_quantite),
                motif=motif,
                effectue_par=request.user,
            )
        except ValueError as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    return Response({'success': True, 'data': _lot_data(lot)})


# ── GET /api/admin/stocks/alertes/ ──────────────────────────────
@extend_schema(tags=['Admin — Stocks'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def alertes_stock(request):
    """Alertes stock actives."""
    niveau = request.query_params.get('niveau', '')

    qs = AlerteStock.objects.filter(
        statut__in=['nouvelle', 'vue']
    ).select_related(
        'produit__producteur__user'
    ).order_by('-created_at')

    if niveau:
        qs = qs.filter(niveau=niveau)

    data = [
        {
            'id':          a.pk,
            'produit':     a.produit.nom,
            'producteur':  a.produit.producteur.user.get_full_name(),
            'niveau':      a.niveau,
            'stock_actuel': a.stock_actuel,
            'seuil':       a.seuil,
            'message':     a.message,
            'statut':      a.statut,
            'created_at':  a.created_at.isoformat(),
        }
        for a in qs
    ]
    return Response({'success': True, 'data': data})


# ── GET /api/admin/stocks/mouvements/ ───────────────────────────
@extend_schema(tags=['Admin — Stocks'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def mouvements_stock(request):
    """Historique des mouvements de stock."""
    qs = MouvementStock.objects.select_related(
        'produit', 'effectue_par'
    ).order_by('-created_at')[:100]

    data = [
        {
            'id':              m.pk,
            'produit':         m.produit.nom,
            'type_mouvement':  m.get_type_mouvement_display(),
            'quantite':        m.quantite,
            'stock_avant':     m.stock_avant,
            'stock_apres':     m.stock_apres,
            'motif':           m.motif,
            'effectue_par':    m.effectue_par.get_full_name() if m.effectue_par else None,
            'created_at':      m.created_at.isoformat(),
        }
        for m in qs
    ]
    return Response({'success': True, 'data': data})
```

---

## ÉTAPE 11 — Vues Collectes Admin

### `apps/api_admin/views/collecte_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.collectes.models import (
    Collecte, ParticipationCollecte,
    ZoneCollecte, PointCollecte
)
from apps.collectes.services.collecte_service import CollecteService
from apps.accounts.models import Producteur


def _collecte_data(c):
    """Sérialisation basique d'une collecte."""
    agent = getattr(c, 'agent_collecte', None) or getattr(c, 'collecteur', None)
    ref   = getattr(c, 'numero_collecte', None) or getattr(c, 'reference', None)
    titre = getattr(c, 'titre', None) or ref
    date  = getattr(c, 'date_prevue', None) or getattr(c, 'date_planifiee', None)

    return {
        'id':                    c.pk,
        'reference':             ref,
        'titre':                 titre,
        'statut':                c.statut,
        'type_collecte':         c.type_collecte,
        'zone':                  c.zone.nom if c.zone else None,
        'date_prevue':           str(date) if date else None,
        'agent':                 agent.get_full_name() if agent else None,
        'nb_producteurs':        c.participations.count(),
        'quantite_prevue_kg':    str(c.quantite_prevue_kg) if c.quantite_prevue_kg else None,
        'quantite_collectee_kg': str(c.quantite_collectee_kg) if c.quantite_collectee_kg else None,
        'created_at':            c.created_at.isoformat(),
    }


# ── GET /api/admin/collectes/ ────────────────────────────────────
@extend_schema(tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def collectes_list(request):
    """Toutes les collectes avec filtre par statut."""
    statut = request.query_params.get('statut', '')

    qs = Collecte.objects.select_related(
        'zone'
    ).prefetch_related('participations').order_by('-created_at')

    if statut:
        qs = qs.filter(statut=statut)

    return Response({
        'success': True,
        'data': [_collecte_data(c) for c in qs]
    })


# ── POST /api/admin/collectes/create/ ───────────────────────────
@extend_schema(tags=['Admin — Collectes'])
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def collecte_create(request):
    """Planifier une nouvelle collecte."""
    zone_id = request.data.get('zone_id')
    zone    = get_object_or_404(ZoneCollecte, pk=zone_id)

    point_id       = request.data.get('point_collecte_id')
    point_collecte = get_object_or_404(
        PointCollecte, pk=point_id
    ) if point_id else None

    agent_id       = request.data.get('agent_id')
    agent_collecte = None
    if agent_id:
        from apps.accounts.models import CustomUser
        agent_collecte = get_object_or_404(CustomUser, pk=agent_id)

    # Récupérer les producteurs
    producteurs_data = []
    for item in request.data.get('producteurs', []):
        p = get_object_or_404(Producteur, pk=item['producteur_id'])
        producteurs_data.append({
            'producteur':       p,
            'quantite_prevue':  item.get('quantite_prevue'),
        })

    try:
        collecte = CollecteService.planifier_collecte(
            titre=request.data.get('titre', ''),
            zone=zone,
            date_prevue=request.data.get('date_prevue'),
            planifie_par=request.user,
            producteurs=producteurs_data,
            point_collecte=point_collecte,
            agent_collecte=agent_collecte,
            instructions=request.data.get('instructions', ''),
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {'success': True, 'data': _collecte_data(collecte)},
        status=status.HTTP_201_CREATED
    )


# ── GET /api/admin/collectes/<id>/ ──────────────────────────────
@extend_schema(tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def collecte_detail(request, pk):
    collecte = get_object_or_404(Collecte, pk=pk)
    return Response({'success': True, 'data': _collecte_data(collecte)})


# ── PATCH /api/admin/collectes/<id>/statut/ ─────────────────────
@extend_schema(tags=['Admin — Collectes'])
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def collecte_statut(request, pk):
    """Démarrer, terminer ou annuler une collecte."""
    collecte = get_object_or_404(Collecte, pk=pk)
    action   = request.data.get('action')

    try:
        if action == 'demarrer':
            CollecteService.demarrer_collecte(collecte, request.user)
        elif action == 'terminer':
            CollecteService.terminer_collecte(
                collecte,
                rapport=request.data.get('rapport', ''),
                quantite_collectee_kg=request.data.get('quantite_collectee_kg'),
            )
        elif action == 'annuler':
            collecte.statut = Collecte.Statut.ANNULEE
            collecte.save()
        else:
            return Response(
                {'success': False, 'error': "Action : demarrer|terminer|annuler"},
                status=status.HTTP_400_BAD_REQUEST
            )
    except ValueError as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({'success': True, 'data': _collecte_data(collecte)})


# ── POST /api/admin/collectes/<id>/participations/ ──────────────
@extend_schema(tags=['Admin — Collectes'])
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def collecte_add_participation(request, pk):
    """Ajouter un producteur à une collecte."""
    collecte     = get_object_or_404(Collecte, pk=pk)
    producteur_id = request.data.get('producteur_id')
    producteur   = get_object_or_404(Producteur, pk=producteur_id)

    part, created = ParticipationCollecte.objects.get_or_create(
        collecte=collecte,
        producteur=producteur,
        defaults={
            'statut': ParticipationCollecte.Statut.INVITE,
        }
    )

    return Response(
        {
            'success': True,
            'data': {
                'id':          part.pk,
                'producteur':  producteur.user.get_full_name(),
                'statut':      part.statut,
                'created':     created,
            }
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )


# ── PATCH /api/admin/collectes/participations/<id>/statut/ ──────
@extend_schema(tags=['Admin — Collectes'])
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def participation_statut(request, pk):
    """Changer le statut d'une participation."""
    part   = get_object_or_404(ParticipationCollecte, pk=pk)
    statut = request.data.get('statut')

    STATUTS = ['invite', 'confirme', 'present', 'absent', 'reporte']
    if statut not in STATUTS:
        return Response(
            {'success': False, 'error': f"Statut invalide : {STATUTS}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    part.statut = statut
    part.save()
    return Response({
        'success': True,
        'data': {'id': part.pk, 'statut': part.statut}
    })


# ── DELETE /api/admin/collectes/participations/<id>/ ────────────
@extend_schema(tags=['Admin — Collectes'])
@api_view(['DELETE'])
@permission_classes([IsSuperAdmin])
def participation_delete(request, pk):
    """Retirer un producteur d'une collecte."""
    part = get_object_or_404(ParticipationCollecte, pk=pk)
    part.delete()
    return Response({
        'success': True,
        'data': {'message': 'Participation supprimée.'}
    })


# ── GET /api/admin/zones/ & /api/admin/points/ ──────────────────
@extend_schema(tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def zones_list(request):
    zones = ZoneCollecte.objects.filter(est_active=True)
    data  = [
        {'id': z.pk, 'nom': z.nom, 'departement': z.departement}
        for z in zones
    ]
    return Response({'success': True, 'data': data})


@extend_schema(tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def zone_detail(request, pk):
    z = get_object_or_404(ZoneCollecte, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id': z.pk, 'nom': z.nom,
            'departement': z.departement,
            'communes': z.liste_communes,
        }
    })


@extend_schema(tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def points_list(request):
    points = PointCollecte.objects.filter(statut='actif')
    data   = [
        {
            'id':      p.pk, 'nom': p.nom,
            'commune': p.commune,
            'adresse': p.adresse,
        }
        for p in points
    ]
    return Response({'success': True, 'data': data})


@extend_schema(tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def point_detail(request, pk):
    p = get_object_or_404(PointCollecte, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id':              p.pk, 'nom': p.nom,
            'commune':         p.commune,
            'departement':     p.departement,
            'adresse':         p.adresse,
            'responsable_nom': p.responsable_nom,
            'responsable_tel': p.responsable_tel,
            'capacite_kg':     p.capacite_kg,
            'statut':          p.statut,
        }
    })
```

---

## ÉTAPE 12 — Vues Config Admin

### `apps/api_admin/views/config_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.home.models import SiteConfig, FAQCategorie, FAQItem, ContactMessage


def _config_data(c):
    return {
        'nom_site':       c.nom_site,
        'slogan':         c.slogan,
        'email_contact':  c.email_contact,
        'telephone':      c.telephone,
        'adresse':        c.adresse,
        'facebook_url':   c.facebook_url,
        'instagram_url':  c.instagram_url,
        'whatsapp_numero': c.whatsapp_numero,
    }


# ── GET/PATCH /api/admin/config/site/ ───────────────────────────
@extend_schema(tags=['Admin — Config'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def site_config(request):
    config = SiteConfig.get_config()

    if request.method == 'GET':
        return Response({'success': True, 'data': _config_data(config)})

    for field in [
        'nom_site', 'slogan', 'email_contact', 'telephone',
        'adresse', 'facebook_url', 'instagram_url', 'whatsapp_numero'
    ]:
        if field in request.data:
            setattr(config, field, request.data[field])
    config.save()
    return Response({'success': True, 'data': _config_data(config)})


# ── GET /api/admin/config/faq/categories/ ───────────────────────
@extend_schema(tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def faq_categories(request):
    cats = FAQCategorie.objects.all().order_by('ordre')
    data = [
        {'id': c.pk, 'titre': c.titre, 'ordre': c.ordre, 'is_active': c.is_active}
        for c in cats
    ]
    return Response({'success': True, 'data': data})


@extend_schema(tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def faq_categorie_detail(request, pk):
    cat   = get_object_or_404(FAQCategorie, pk=pk)
    items = FAQItem.objects.filter(categorie=cat, is_active=True)
    return Response({
        'success': True,
        'data': {
            'id':     cat.pk,
            'titre':  cat.titre,
            'items':  [
                {'id': i.pk, 'question': i.question, 'reponse': i.reponse}
                for i in items
            ]
        }
    })


# ── GET /api/admin/config/faq/items/ ────────────────────────────
@extend_schema(tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def faq_items(request):
    items = FAQItem.objects.select_related('categorie').order_by('ordre')
    data  = [
        {
            'id':        i.pk,
            'categorie': i.categorie.titre,
            'question':  i.question,
            'reponse':   i.reponse,
            'is_active': i.is_active,
        }
        for i in items
    ]
    return Response({'success': True, 'data': data})


@extend_schema(tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def faq_item_detail(request, pk):
    i = get_object_or_404(FAQItem, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id':        i.pk,
            'categorie': i.categorie.titre,
            'question':  i.question,
            'reponse':   i.reponse,
        }
    })


# ── GET /api/admin/config/contact/ ──────────────────────────────
@extend_schema(tags=['Admin — Config'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def contact_messages(request):
    msgs = ContactMessage.objects.order_by('-created_at')[:50]
    data = [
        {
            'id':         m.pk,
            'nom':        m.nom,
            'email':      m.email,
            'sujet':      m.sujet,
            'message':    m.message,
            'statut':     m.statut,
            'created_at': m.created_at.isoformat(),
        }
        for m in msgs
    ]
    return Response({'success': True, 'data': data})


@extend_schema(tags=['Admin — Config'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def contact_message_detail(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': {
                'id':      msg.pk,
                'nom':     msg.nom,
                'email':   msg.email,
                'sujet':   msg.sujet,
                'message': msg.message,
                'statut':  msg.statut,
            }
        })

    nouveau_statut = request.data.get('statut')
    STATUTS        = ['nouveau', 'lu', 'repondu', 'archive']
    if nouveau_statut and nouveau_statut in STATUTS:
        msg.statut = nouveau_statut
        msg.save()

    return Response({'success': True, 'data': {'id': msg.pk, 'statut': msg.statut}})
```

---

## ÉTAPE 13 — Vues Acheteurs & Vouchers Admin

### `apps/api_admin/views/acheteur_views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.accounts.models import Acheteur
from apps.payments.models import Voucher, ProgrammeVoucher
from apps.payments.serializers import VoucherSerializer


@extend_schema(tags=['Admin — Acheteurs'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def acheteurs_list(request):
    qs   = Acheteur.objects.select_related('user').order_by('-created_at')
    data = [
        {
            'id':              a.pk,
            'nom':             a.user.get_full_name(),
            'email':           a.user.email,
            'telephone':       a.user.telephone,
            'type_acheteur':   a.get_type_acheteur_display(),
            'total_commandes': a.total_commandes,
            'total_depense':   str(a.total_depense),
            'created_at':      a.created_at.isoformat(),
        }
        for a in qs
    ]
    return Response({'success': True, 'data': data})


@extend_schema(tags=['Admin — Acheteurs'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def acheteur_detail(request, pk):
    a = get_object_or_404(Acheteur, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id':            a.pk,
            'nom':           a.user.get_full_name(),
            'email':         a.user.email,
            'telephone':     a.user.telephone,
            'type_acheteur': a.get_type_acheteur_display(),
            'adresse':       a.adresse,
            'ville':         a.ville,
            'departement':   a.departement,
        }
    })


@extend_schema(tags=['Admin — Vouchers'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def vouchers_list(request):
    qs = Voucher.objects.select_related('programme', 'beneficiaire__user')
    return Response({
        'success': True,
        'data': VoucherSerializer(qs, many=True).data
    })


@extend_schema(tags=['Admin — Vouchers'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def voucher_detail(request, pk):
    v = get_object_or_404(Voucher, pk=pk)
    return Response({'success': True, 'data': VoucherSerializer(v).data})


@extend_schema(tags=['Admin — Vouchers'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def programmes_list(request):
    progs = ProgrammeVoucher.objects.all()
    data  = [
        {
            'id':             p.pk,
            'nom':            p.nom,
            'code_programme': p.code_programme,
            'type_programme': p.get_type_programme_display(),
            'budget_total':   str(p.budget_total) if p.budget_total else None,
            'budget_utilise': str(p.budget_utilise),
            'est_en_cours':   p.est_en_cours,
            'is_active':      p.is_active,
        }
        for p in progs
    ]
    return Response({'success': True, 'data': data})


@extend_schema(tags=['Admin — Vouchers'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def programme_detail(request, pk):
    p = get_object_or_404(ProgrammeVoucher, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id':             p.pk,
            'nom':            p.nom,
            'code_programme': p.code_programme,
            'description':    p.description,
            'budget_total':   str(p.budget_total) if p.budget_total else None,
            'budget_utilise': str(p.budget_utilise),
            'budget_restant': str(p.budget_restant) if p.budget_restant else None,
            'nb_vouchers':    p.vouchers.count(),
        }
    })


@extend_schema(tags=['Admin — Adresses'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def adresses_list_admin(request):
    from apps.accounts.models import Adresse
    from apps.accounts.serializers import AdresseSerializer
    qs = Adresse.objects.select_related('user').order_by('-created_at')
    return Response({
        'success': True,
        'data': AdresseSerializer(qs, many=True).data
    })
```

---

## ÉTAPE 14 — `apps/api_admin/views/__init__.py`

```python
from .stats_views      import global_stats, admin_options
from .user_views       import users_list, user_create, user_detail, user_toggle
from .producteur_views import (
    producteurs_list, producteur_create,
    producteur_detail, producteur_statut,
)
from .commande_views   import commandes_list, commande_detail, commande_statut
from .paiement_views   import paiements_list, paiement_statut
from .catalogue_views  import (
    catalogue_list, catalogue_create,
    catalogue_detail, catalogue_statut, catalogue_toggle,
    categories_admin, categorie_detail,
)
from .stock_views      import (
    lots_list, lot_create, lot_detail,
    alertes_stock, mouvements_stock,
)
from .collecte_views   import (
    collectes_list, collecte_create, collecte_detail,
    collecte_statut, collecte_add_participation,
    participation_statut, participation_delete,
    zones_list, zone_detail, points_list, point_detail,
)
from .config_views     import (
    site_config,
    faq_categories, faq_categorie_detail,
    faq_items, faq_item_detail,
    contact_messages, contact_message_detail,
)
from .acheteur_views   import (
    acheteurs_list, acheteur_detail,
    vouchers_list, voucher_detail,
    programmes_list, programme_detail,
    adresses_list_admin,
)
```

---

## ÉTAPE 15 — URLs Superadmin

### `apps/api_admin/urls.py`

```python
from django.urls import path
from apps.api_admin import views

app_name = 'api_admin'

urlpatterns = [

    # ── Stats ───────────────────────────────────────────────────
    path('stats/',          views.global_stats,    name='stats'),
    path('options/',        views.admin_options,   name='options'),

    # ── Utilisateurs ────────────────────────────────────────────
    path('users/',                   views.users_list,   name='users_list'),
    path('users/create/',            views.user_create,  name='user_create'),
    path('users/<int:pk>/detail/',   views.user_detail,  name='user_detail'),
    path('users/<int:pk>/toggle/',   views.user_toggle,  name='user_toggle'),

    # ── Producteurs ─────────────────────────────────────────────
    path('producteurs/',                      views.producteurs_list,    name='producteurs_list'),
    path('producteurs/create/',               views.producteur_create,   name='producteur_create'),
    path('producteurs/<int:pk>/detail/',      views.producteur_detail,   name='producteur_detail'),
    path('producteurs/<int:pk>/statut/',      views.producteur_statut,   name='producteur_statut'),

    # ── Commandes ───────────────────────────────────────────────
    path('commandes/',                        views.commandes_list,      name='commandes_list'),
    path('commandes/<str:numero>/',           views.commande_detail,     name='commande_detail'),
    path('commandes/<str:numero>/statut/',    views.commande_statut,     name='commande_statut'),

    # ── Paiements ───────────────────────────────────────────────
    path('paiements/',                        views.paiements_list,      name='paiements_list'),
    path('paiements/<int:pk>/statut/',        views.paiement_statut,     name='paiement_statut'),

    # ── Catalogue ───────────────────────────────────────────────
    path('catalogue/',                        views.catalogue_list,      name='catalogue_list'),
    path('catalogue/create/',                 views.catalogue_create,    name='catalogue_create'),
    path('catalogue/<int:pk>/detail/',        views.catalogue_detail,    name='catalogue_detail'),
    path('catalogue/<int:pk>/statut/',        views.catalogue_statut,    name='catalogue_statut'),
    path('catalogue/<int:pk>/toggle/',        views.catalogue_toggle,    name='catalogue_toggle'),
    path('categories/',                       views.categories_admin,    name='categories_admin'),
    path('categories/<int:pk>/',              views.categorie_detail,    name='categorie_detail'),

    # ── Stocks ──────────────────────────────────────────────────
    path('stocks/lots/',                      views.lots_list,           name='lots_list'),
    path('stocks/lots/create/',               views.lot_create,          name='lot_create'),
    path('stocks/lots/<int:pk>/',             views.lot_detail,          name='lot_detail'),
    path('stocks/alertes/',                   views.alertes_stock,       name='alertes_stock'),
    path('stocks/mouvements/',                views.mouvements_stock,    name='mouvements_stock'),

    # ── Collectes ───────────────────────────────────────────────
    path('collectes/',                        views.collectes_list,              name='collectes_list'),
    path('collectes/create/',                 views.collecte_create,             name='collecte_create'),
    path('collectes/<int:pk>/',               views.collecte_detail,             name='collecte_detail'),
    path('collectes/<int:pk>/statut/',        views.collecte_statut,             name='collecte_statut'),
    path('collectes/<int:pk>/participations/', views.collecte_add_participation,  name='add_participation'),
    path('collectes/participations/<int:pk>/statut/', views.participation_statut, name='participation_statut'),
    path('collectes/participations/<int:pk>/', views.participation_delete,        name='participation_delete'),
    path('zones/',                            views.zones_list,                  name='zones_list'),
    path('zones/<int:pk>/',                   views.zone_detail,                 name='zone_detail'),
    path('points/',                           views.points_list,                 name='points_list'),
    path('points/<int:pk>/',                  views.point_detail,                name='point_detail'),

    # ── Config ──────────────────────────────────────────────────
    path('config/site/',                      views.site_config,             name='site_config'),
    path('config/faq/categories/',            views.faq_categories,          name='faq_categories'),
    path('config/faq/categories/<int:pk>/',   views.faq_categorie_detail,    name='faq_categorie_detail'),
    path('config/faq/items/',                 views.faq_items,               name='faq_items'),
    path('config/faq/items/<int:pk>/',        views.faq_item_detail,         name='faq_item_detail'),
    path('config/contact/',                   views.contact_messages,        name='contact_messages'),
    path('config/contact/<int:pk>/',          views.contact_message_detail,  name='contact_detail'),

    # ── Acheteurs, Vouchers, Adresses ───────────────────────────
    path('acheteurs/',                        views.acheteurs_list,          name='acheteurs_list'),
    path('acheteurs/<int:pk>/',               views.acheteur_detail,         name='acheteur_detail'),
    path('vouchers/',                         views.vouchers_list,           name='vouchers_list'),
    path('vouchers/<int:pk>/',                views.voucher_detail,          name='voucher_detail'),
    path('vouchers/programmes/',              views.programmes_list,         name='programmes_list'),
    path('vouchers/programmes/<int:pk>/',     views.programme_detail,        name='programme_detail'),
    path('adresses/',                         views.adresses_list_admin,     name='adresses_admin'),
]
```

---

## ÉTAPE 16 — Ajouter dans `config/urls.py`

```python
path('api/admin/', include('apps.api_admin.urls')),
```

---

## ÉTAPE 17 — Endpoints système (healthcheck, contact public, FAQ publique)

### Ajouter dans `apps/home/views.py`

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
import json


def health_check(request):
    """Railway healthcheck."""
    return JsonResponse({'status': 'ok', 'service': 'Makèt Peyizan'})


def faq_publique(request):
    """FAQ publique accessible sans authentification."""
    from apps.home.models import FAQCategorie
    cats = FAQCategorie.objects.filter(is_active=True).prefetch_related(
        'items'
    ).order_by('ordre')
    data = [
        {
            'categorie': c.titre,
            'items': [
                {'question': i.question, 'reponse': i.reponse}
                for i in c.items.filter(is_active=True)
            ]
        }
        for c in cats
    ]
    return JsonResponse({'success': True, 'data': data})


@csrf_exempt
def contact_public(request):
    """Formulaire de contact public."""
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'error': 'Méthode POST requise.'},
            status=405
        )

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    nom     = data.get('nom', '').strip()
    email   = data.get('email', '').strip()
    message = data.get('message', '').strip()

    if not nom or not email or not message:
        return JsonResponse(
            {'success': False, 'error': 'Nom, email et message sont requis.'},
            status=400
        )

    from apps.home.models import ContactMessage
    ContactMessage.objects.create(
        nom=nom,
        email=email,
        sujet=data.get('sujet', ''),
        message=message,
    )

    return JsonResponse({
        'success': True,
        'data': {'message': 'Message envoyé. Nous vous répondrons bientôt.'}
    }, status=201)
```

### Ajouter dans `apps/home/urls.py`

```python
from django.urls import path
from apps.home import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='index'),
]
```

### Ajouter dans `config/urls.py`

```python
from apps.home.views import health_check, faq_publique, contact_public

urlpatterns = [
    path('health/',    health_check,    name='health'),
    path('faq/',       faq_publique,    name='faq'),
    path('contact/',   contact_public,  name='contact'),
    # ... reste des urls
]
```

---

## ÉTAPE 18 — Migrations et vérification finale

```bash
# Migrations
python manage.py makemigrations home api_admin --settings=config.settings.development
python manage.py migrate --settings=config.settings.development

# Vérification
python manage.py check --settings=config.settings.development

# Lancer
python manage.py runserver --settings=config.settings.development

# Swagger — vérifier que tous les endpoints apparaissent
# http://localhost:8000/api/schema/swagger-ui/
```

---

## RÉSUMÉ — Endpoints créés dans ce prompt

### Stats & Options
| GET | `/api/admin/stats/` |
| GET | `/api/admin/options/?type=...` |

### Utilisateurs (4) · Producteurs (4) · Commandes (3)
### Paiements (2) · Catalogue (7) · Stocks (5)
### Collectes (9) · Config (6) · Acheteurs/Vouchers/Adresses (7)

**Total : ~50 endpoints superadmin + 3 endpoints système publics**

L'ensemble de l'API documentée dans `API.md` est maintenant **complètement implémentée**.
