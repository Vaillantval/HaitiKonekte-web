# PROMPT CLAUDE CODE — Makèt Peyizan
# API REST — Partie 2 : Catalogue, Panier, Commander

---

## CONTEXTE

Tu travailles sur **Makèt Peyizan** (marketplace agricole haïtienne).
La Partie 1 (Auth, Adresses, Dashboard Producteur) est déjà implémentée.

Tu vas maintenant implémenter :
- **Catalogue public** : listing filtré, détail produit, catégories
- **Mes produits** : CRUD producteur
- **Panier** : DB-backed, lié au compte JWT
- **Commander** : créer commandes depuis le panier (cash, MonCash, hors-ligne)

**Format de réponse uniforme :**
- Succès : `{ "success": true, "data": {...} }`
- Erreur  : `{ "success": false, "error": "message" }`

---

## FICHIERS À CRÉER

```
apps/catalog/
├── serializers/
│   ├── __init__.py
│   ├── categorie_serializers.py
│   └── produit_serializers.py
├── views/
│   ├── __init__.py
│   ├── public_views.py       → catalogue public + catégories
│   └── producteur_views.py   → mes-produits CRUD
├── filters.py                → filtres DRF pour les produits
└── urls.py                   ← remplacer le fichier vide

apps/orders/
├── models/
│   └── panier.py             → nouveau modèle Panier + LignePanier
├── serializers/
│   ├── __init__.py
│   ├── panier_serializers.py
│   └── commande_serializers.py
├── views/
│   ├── __init__.py
│   ├── panier_views.py
│   └── commande_views.py
└── urls.py                   ← remplacer le fichier vide
```

---

## ÉTAPE 1 — Modèle Panier (nouveau)

### `apps/orders/models/panier.py`

```python
from django.db import models
from django.conf import settings


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
        verbose_name        = 'Panier'
        verbose_name_plural = 'Paniers'

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
        verbose_name        = 'Ligne panier'
        verbose_name_plural = 'Lignes panier'
        unique_together     = ('panier', 'produit')

    def __str__(self):
        return f"{self.produit.nom} x{self.quantite}"

    @property
    def sous_total(self):
        return self.produit.prix_unitaire * self.quantite
```

### Mettre à jour `apps/orders/models/__init__.py`

```python
from .commande        import Commande
from .commande_detail import CommandeDetail, HistoriqueStatutCommande
from .panier          import Panier, LignePanier

__all__ = [
    'Commande', 'CommandeDetail', 'HistoriqueStatutCommande',
    'Panier', 'LignePanier'
]
```

---

## ÉTAPE 2 — Filtres catalogue

### `apps/catalog/filters.py`

```python
import django_filters
from apps.catalog.models import Produit


class ProduitFilter(django_filters.FilterSet):
    search      = django_filters.CharFilter(method='filter_search')
    categorie   = django_filters.CharFilter(field_name='categorie__slug')
    departement = django_filters.CharFilter(
                    field_name='producteur__departement'
                  )
    producteur_id = django_filters.NumberFilter(
                      field_name='producteur__id'
                    )
    prix_min    = django_filters.NumberFilter(
                    field_name='prix_unitaire', lookup_expr='gte'
                  )
    prix_max    = django_filters.NumberFilter(
                    field_name='prix_unitaire', lookup_expr='lte'
                  )
    featured    = django_filters.BooleanFilter(field_name='is_featured')

    class Meta:
        model  = Produit
        fields = [
            'categorie', 'departement', 'producteur_id',
            'prix_min', 'prix_max', 'featured'
        ]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(nom__icontains=value)         |
            Q(variete__icontains=value)     |
            Q(description__icontains=value) |
            Q(origine__icontains=value)     |
            Q(categorie__nom__icontains=value) |
            Q(producteur__commune__icontains=value)
        )
```

---

## ÉTAPE 3 — Serializers Catalogue

### `apps/catalog/serializers/categorie_serializers.py`

```python
from rest_framework import serializers
from apps.catalog.models import Categorie


class CategorieSerializer(serializers.ModelSerializer):
    nb_produits = serializers.SerializerMethodField()

    class Meta:
        model  = Categorie
        fields = ['id', 'nom', 'slug', 'description',
                  'image', 'icone', 'ordre', 'nb_produits']

    def get_nb_produits(self, obj):
        return obj.nb_produits
```

---

### `apps/catalog/serializers/produit_serializers.py`

```python
from rest_framework import serializers
from apps.catalog.models import Produit, ImageProduit, Categorie


class ImageProduitSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ImageProduit
        fields = ['id', 'image', 'legende', 'ordre']


class ProducteurMinimalSerializer(serializers.Serializer):
    """Représentation minimale du producteur dans un produit."""
    id          = serializers.IntegerField(source='pk')
    nom         = serializers.SerializerMethodField()
    commune     = serializers.CharField()
    departement = serializers.CharField()
    code        = serializers.CharField(source='code_producteur')

    def get_nom(self, obj):
        return obj.user.get_full_name()


class ProduitListSerializer(serializers.ModelSerializer):
    """Serializer allégé pour la liste du catalogue."""
    categorie   = serializers.SerializerMethodField()
    producteur  = serializers.SerializerMethodField()
    unite_vente_label = serializers.CharField(
                          source='get_unite_vente_display'
                        )

    class Meta:
        model  = Produit
        fields = [
            'id', 'nom', 'slug', 'variete',
            'prix_unitaire', 'prix_gros',
            'unite_vente', 'unite_vente_label',
            'quantite_min_commande', 'stock_reel',
            'is_featured', 'image_principale',
            'categorie', 'producteur', 'created_at'
        ]

    def get_categorie(self, obj):
        return {'nom': obj.categorie.nom, 'slug': obj.categorie.slug}

    def get_producteur(self, obj):
        return {
            'id':          obj.producteur.pk,
            'nom':         obj.producteur.user.get_full_name(),
            'commune':     obj.producteur.commune,
            'departement': obj.producteur.departement,
        }


class ProduitDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour le détail d'un produit."""
    categorie         = serializers.SerializerMethodField()
    producteur        = serializers.SerializerMethodField()
    images            = ImageProduitSerializer(many=True, read_only=True)
    unite_vente_label = serializers.CharField(
                          source='get_unite_vente_display'
                        )
    similaires        = serializers.SerializerMethodField()
    qr_code_url       = serializers.SerializerMethodField()

    class Meta:
        model  = Produit
        fields = [
            'id', 'nom', 'slug', 'variete', 'description',
            'prix_unitaire', 'prix_gros',
            'unite_vente', 'unite_vente_label',
            'quantite_min_commande', 'stock_disponible', 'stock_reel',
            'is_featured', 'image_principale', 'qr_code_url',
            'origine', 'saison', 'certifications',
            'categorie', 'producteur', 'images',
            'similaires', 'created_at'
        ]

    def get_categorie(self, obj):
        return {
            'id':   obj.categorie.pk,
            'nom':  obj.categorie.nom,
            'slug': obj.categorie.slug,
        }

    def get_producteur(self, obj):
        p = obj.producteur
        return {
            'id':               p.pk,
            'nom':              p.user.get_full_name(),
            'commune':          p.commune,
            'departement':      p.departement,
            'code_producteur':  p.code_producteur,
            'telephone':        p.user.telephone,
            'nb_produits':      p.nb_produits_actifs,
        }

    def get_similaires(self, obj):
        similaires = Produit.objects.filter(
            categorie=obj.categorie,
            is_active=True,
            stock_disponible__gt=0
        ).exclude(pk=obj.pk)[:4]
        return ProduitListSerializer(
            similaires, many=True,
            context=self.context
        ).data

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
        return None


class ProduitCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/modifier un produit (producteur)."""

    class Meta:
        model  = Produit
        fields = [
            'nom', 'categorie', 'variete', 'description',
            'prix_unitaire', 'prix_gros',
            'unite_vente', 'quantite_min_commande',
            'stock_disponible', 'seuil_alerte',
            'image_principale',
            'origine', 'saison', 'certifications',
            'is_active'
        ]

    def validate_prix_unitaire(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Le prix doit être supérieur à 0."
            )
        return value

    def validate_stock_disponible(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Le stock ne peut pas être négatif."
            )
        return value
```

---

### `apps/catalog/serializers/__init__.py`

```python
from .categorie_serializers import CategorieSerializer
from .produit_serializers   import (
    ProduitListSerializer,
    ProduitDetailSerializer,
    ProduitCreateUpdateSerializer,
    ImageProduitSerializer,
)

__all__ = [
    'CategorieSerializer',
    'ProduitListSerializer',
    'ProduitDetailSerializer',
    'ProduitCreateUpdateSerializer',
    'ImageProduitSerializer',
]
```

---

## ÉTAPE 4 — Vues catalogue public

### `apps/catalog/views/public_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.shortcuts import get_object_or_404

from apps.catalog.models import Produit, Categorie
from apps.catalog.serializers import (
    ProduitListSerializer,
    ProduitDetailSerializer,
    CategorieSerializer,
)
from apps.catalog.filters import ProduitFilter


class ProduitPagination(PageNumberPagination):
    page_size              = 20
    page_size_query_param  = 'page_size'
    max_page_size          = 100


# ── GET /api/products/ ──────────────────────────────────────────
@extend_schema(tags=['Catalogue'], summary='Liste des produits')
@api_view(['GET'])
@permission_classes([AllowAny])
def produits_list(request):
    """
    Liste paginée des produits actifs avec filtres.
    Filtres : search, categorie, departement, producteur_id,
              prix_min, prix_max, featured, page, page_size
    """
    qs = Produit.objects.filter(
        is_active=True,
        stock_disponible__gt=0
    ).select_related(
        'categorie',
        'producteur__user'
    ).order_by('-is_featured', '-created_at')

    # Appliquer les filtres
    filterset = ProduitFilter(request.query_params, queryset=qs)
    if not filterset.is_valid():
        return Response(
            {'success': False, 'error': filterset.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    qs = filterset.qs

    # Pagination
    paginator   = ProduitPagination()
    page        = paginator.paginate_queryset(qs, request)
    serializer  = ProduitListSerializer(
                    page, many=True,
                    context={'request': request}
                  )

    return Response({
        'success': True,
        'data': {
            'count':    paginator.page.paginator.count,
            'next':     paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results':  serializer.data,
        }
    })


# ── GET /api/products/public/<slug>/ ────────────────────────────
@extend_schema(tags=['Catalogue'], summary='Détail produit')
@api_view(['GET'])
@permission_classes([AllowAny])
def produit_detail(request, slug):
    """Détail complet d'un produit avec galerie et similaires."""
    produit    = get_object_or_404(Produit, slug=slug, is_active=True)
    serializer = ProduitDetailSerializer(
                   produit,
                   context={'request': request}
                 )
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/products/categories/ ──────────────────────────────
@extend_schema(tags=['Catalogue'], summary='Liste des catégories')
@api_view(['GET'])
@permission_classes([AllowAny])
def categories_list(request):
    """Toutes les catégories actives."""
    categories = Categorie.objects.filter(
        is_active=True
    ).order_by('ordre', 'nom')
    serializer = CategorieSerializer(categories, many=True)
    return Response({'success': True, 'data': serializer.data})
```

---

## ÉTAPE 5 — Vues produits producteur

### `apps/catalog/views/producteur_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsProducteur
from apps.catalog.models import Produit, ImageProduit
from apps.catalog.serializers import (
    ProduitListSerializer,
    ProduitDetailSerializer,
    ProduitCreateUpdateSerializer,
)


# ── GET/POST /api/products/mes-produits/ ────────────────────────
@extend_schema(tags=['Mes Produits'])
@api_view(['GET', 'POST'])
@permission_classes([IsProducteur])
def mes_produits(request):
    producteur = request.user.profil_producteur

    if request.method == 'GET':
        qs = Produit.objects.filter(
            producteur=producteur
        ).select_related('categorie').order_by('-created_at')

        serializer = ProduitListSerializer(
            qs, many=True, context={'request': request}
        )
        return Response({'success': True, 'data': serializer.data})

    # POST — créer un produit
    serializer = ProduitCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Statut automatique selon producteur actif
    statut = 'actif' if producteur.statut == 'actif' else 'en_attente'
    produit = serializer.save(
        producteur=producteur,
        statut=statut,
        is_active=(producteur.statut == 'actif')
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


# ── GET/PATCH/DELETE /api/products/mes-produits/<slug>/ ─────────
@extend_schema(tags=['Mes Produits'])
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsProducteur])
def mon_produit_detail(request, slug):
    producteur = request.user.profil_producteur
    produit    = get_object_or_404(
                   Produit, slug=slug, producteur=producteur
                 )

    if request.method == 'GET':
        serializer = ProduitDetailSerializer(
            produit, context={'request': request}
        )
        return Response({'success': True, 'data': serializer.data})

    if request.method == 'PATCH':
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

    # DELETE
    produit.delete()
    return Response({
        'success': True,
        'data': {'message': 'Produit supprimé avec succès.'}
    })
```

---

### `apps/catalog/views/__init__.py`

```python
from .public_views     import produits_list, produit_detail, categories_list
from .producteur_views import mes_produits, mon_produit_detail

__all__ = [
    'produits_list', 'produit_detail', 'categories_list',
    'mes_produits', 'mon_produit_detail',
]
```

---

## ÉTAPE 6 — URLs Catalogue

### `apps/catalog/urls.py` ← REMPLACER le fichier vide

```python
from django.urls import path
from apps.catalog import views

app_name = 'catalog'

urlpatterns = [
    # Catalogue public
    path('',                        views.produits_list,    name='produits_list'),
    path('categories/',             views.categories_list,  name='categories_list'),
    path('public/<slug:slug>/',     views.produit_detail,   name='produit_detail'),

    # Mes produits (producteur connecté)
    path('mes-produits/',                   views.mes_produits,        name='mes_produits'),
    path('mes-produits/<slug:slug>/',       views.mon_produit_detail,  name='mon_produit_detail'),
]
```

---

## ÉTAPE 7 — Serializers Panier

### `apps/orders/serializers/panier_serializers.py`

```python
from rest_framework import serializers
from apps.orders.models import Panier, LignePanier


class LignePanierSerializer(serializers.ModelSerializer):
    """Ligne de panier enrichie avec les infos produit."""
    slug             = serializers.CharField(source='produit.slug')
    nom              = serializers.CharField(source='produit.nom')
    prix_unitaire    = serializers.DecimalField(
                         source='produit.prix_unitaire',
                         max_digits=10, decimal_places=2
                       )
    unite_vente      = serializers.CharField(source='produit.unite_vente')
    producteur_id    = serializers.IntegerField(
                         source='produit.producteur.pk'
                       )
    producteur_nom   = serializers.SerializerMethodField()
    image            = serializers.SerializerMethodField()
    stock_reel       = serializers.IntegerField(source='produit.stock_reel')

    class Meta:
        model  = LignePanier
        fields = [
            'id', 'slug', 'nom', 'quantite',
            'prix_unitaire', 'sous_total',
            'unite_vente', 'producteur_id',
            'producteur_nom', 'image', 'stock_reel'
        ]

    def get_producteur_nom(self, obj):
        return obj.produit.producteur.user.get_full_name()

    def get_image(self, obj):
        if obj.produit.image_principale:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(
                    obj.produit.image_principale.url
                )
        return None


class PanierSerializer(serializers.ModelSerializer):
    """Résumé complet du panier."""
    items        = LignePanierSerializer(many=True, read_only=True)
    producteurs  = serializers.SerializerMethodField()

    class Meta:
        model  = Panier
        fields = [
            'items', 'total', 'nb_articles',
            'nb_items', 'producteurs'
        ]

    def get_producteurs(self, obj):
        seen = {}
        for item in obj.items.select_related(
            'produit__producteur__user'
        ).all():
            p = item.produit.producteur
            if p.pk not in seen:
                seen[p.pk] = {
                    'id':  p.pk,
                    'nom': p.user.get_full_name(),
                }
        return list(seen.values())
```

---

## ÉTAPE 8 — Serializers Commande

### `apps/orders/serializers/commande_serializers.py`

```python
from rest_framework import serializers
from apps.accounts.models import Adresse


class PasserCommandeSerializer(serializers.Serializer):
    """Données pour passer une commande depuis le panier."""

    METHODES = ['cash', 'moncash', 'hors_ligne']
    MODES    = ['domicile', 'collecte', 'retrait']

    methode_paiement     = serializers.ChoiceField(choices=METHODES)
    mode_livraison       = serializers.ChoiceField(choices=MODES)

    # Adresse — soit un ID soit du texte libre
    adresse_livraison_id = serializers.IntegerField(
                             required=False, allow_null=True
                           )
    adresse_livraison_text = serializers.CharField(
                               required=False, allow_blank=True
                             )
    ville_livraison      = serializers.CharField(
                             required=False, allow_blank=True
                           )
    departement_livraison = serializers.CharField(
                              required=False, allow_blank=True
                            )

    # Preuve de paiement (hors ligne)
    preuve_paiement      = serializers.ImageField(
                             required=False, allow_null=True
                           )

    notes                = serializers.CharField(
                             required=False, allow_blank=True
                           )

    def validate(self, data):
        mode = data.get('mode_livraison')
        if mode == 'domicile':
            addr_id   = data.get('adresse_livraison_id')
            addr_text = data.get('adresse_livraison_text')
            if not addr_id and not addr_text:
                raise serializers.ValidationError(
                    "Une adresse de livraison est requise "
                    "pour la livraison à domicile."
                )
        return data
```

---

### `apps/orders/serializers/__init__.py`

```python
from .panier_serializers   import PanierSerializer, LignePanierSerializer
from .commande_serializers import PasserCommandeSerializer

__all__ = [
    'PanierSerializer', 'LignePanierSerializer',
    'PasserCommandeSerializer',
]
```

---

## ÉTAPE 9 — Vues Panier

### `apps/orders/views/panier_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.orders.models import Panier, LignePanier
from apps.orders.serializers import PanierSerializer
from apps.catalog.models import Produit


def _get_or_create_panier(user):
    """Récupère ou crée le panier de l'utilisateur."""
    panier, _ = Panier.objects.get_or_create(user=user)
    return panier


def _panier_response(panier, request):
    """Retourne la réponse standardisée du panier."""
    serializer = PanierSerializer(panier, context={'request': request})
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/orders/panier/ ──────────────────────────────────────
@extend_schema(tags=['Panier'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def panier_resume(request):
    """Résumé du panier de l'utilisateur connecté."""
    panier = _get_or_create_panier(request.user)
    return _panier_response(panier, request)


# ── POST /api/orders/panier/ajouter/ ───────────────────────────
@extend_schema(tags=['Panier'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def panier_ajouter(request):
    """
    Ajouter un produit au panier.
    Body : { "slug": "banane-ti-malice", "quantite": 2 }
    """
    slug     = request.data.get('slug')
    quantite = int(request.data.get('quantite', 1))

    if not slug:
        return Response(
            {'success': False, 'error': "Le champ 'slug' est requis."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if quantite <= 0:
        return Response(
            {'success': False, 'error': "La quantité doit être supérieure à 0."},
            status=status.HTTP_400_BAD_REQUEST
        )

    produit = get_object_or_404(Produit, slug=slug, is_active=True)

    # Vérifier le stock
    if produit.stock_reel < quantite:
        return Response(
            {
                'success': False,
                'error': (
                    f"Stock insuffisant pour '{produit.nom}'. "
                    f"Disponible : {produit.stock_reel} "
                    f"{produit.get_unite_vente_display()}."
                )
            },
            status=status.HTTP_409_CONFLICT
        )

    panier = _get_or_create_panier(request.user)

    # Ajouter ou mettre à jour la ligne
    ligne, created = LignePanier.objects.get_or_create(
        panier=panier,
        produit=produit,
        defaults={'quantite': quantite}
    )

    if not created:
        new_qty = ligne.quantite + quantite
        if produit.stock_reel < new_qty:
            return Response(
                {
                    'success': False,
                    'error': (
                        f"Stock insuffisant. "
                        f"Vous avez déjà {ligne.quantite} "
                        f"{produit.get_unite_vente_display()} dans votre panier."
                    )
                },
                status=status.HTTP_409_CONFLICT
            )
        ligne.quantite = new_qty
        ligne.save()

    return _panier_response(panier, request)


# ── PATCH /api/orders/panier/modifier/<slug>/ ───────────────────
@extend_schema(tags=['Panier'])
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def panier_modifier(request, slug):
    """
    Modifier la quantité d'un article dans le panier.
    Body : { "quantite": 3 }
    """
    quantite = int(request.data.get('quantite', 0))

    if quantite <= 0:
        return Response(
            {'success': False, 'error': "La quantité doit être supérieure à 0."},
            status=status.HTTP_400_BAD_REQUEST
        )

    produit = get_object_or_404(Produit, slug=slug, is_active=True)
    panier  = get_object_or_404(Panier, user=request.user)
    ligne   = get_object_or_404(LignePanier, panier=panier, produit=produit)

    # Vérifier le stock
    if produit.stock_reel < quantite:
        return Response(
            {
                'success': False,
                'error': (
                    f"Stock insuffisant. "
                    f"Disponible : {produit.stock_reel} "
                    f"{produit.get_unite_vente_display()}."
                )
            },
            status=status.HTTP_409_CONFLICT
        )

    ligne.quantite = quantite
    ligne.save()

    return _panier_response(panier, request)


# ── DELETE /api/orders/panier/retirer/<slug>/ ───────────────────
@extend_schema(tags=['Panier'])
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def panier_retirer(request, slug):
    """Retirer un produit du panier."""
    produit = get_object_or_404(Produit, slug=slug)
    panier  = get_object_or_404(Panier, user=request.user)
    ligne   = get_object_or_404(LignePanier, panier=panier, produit=produit)

    ligne.delete()
    return _panier_response(panier, request)


# ── DELETE /api/orders/panier/vider/ ───────────────────────────
@extend_schema(tags=['Panier'])
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def panier_vider(request):
    """Vider entièrement le panier."""
    panier = get_object_or_404(Panier, user=request.user)
    panier.items.all().delete()
    return _panier_response(panier, request)
```

---

## ÉTAPE 10 — Vues Commander

### `apps/orders/views/commande_views.py`

```python
from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsAcheteur
from apps.accounts.models import Adresse
from apps.orders.models import Panier, Commande
from apps.orders.serializers import PasserCommandeSerializer
from apps.orders.services.commande_service import CommandeService
from apps.payments.models import Paiement
from apps.payments.services.paiement_service import PaiementService
from apps.payments.services.moncash_service import MonCashService


# ── POST /api/orders/commander/ ─────────────────────────────────
@extend_schema(tags=['Commander'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def commander(request):
    """
    Passer commande depuis le panier.
    Crée une commande par producteur présent dans le panier.
    """
    # Vérifier le rôle acheteur
    if not hasattr(request.user, 'profil_acheteur'):
        return Response(
            {'success': False, 'error': "Seuls les acheteurs peuvent passer commande."},
            status=status.HTTP_403_FORBIDDEN
        )

    acheteur = request.user.profil_acheteur

    # Valider les données
    serializer = PasserCommandeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    data = serializer.validated_data

    # Récupérer le panier
    try:
        panier = Panier.objects.prefetch_related(
            'items__produit__producteur__user'
        ).get(user=request.user)
    except Panier.DoesNotExist:
        return Response(
            {'success': False, 'error': "Votre panier est vide."},
            status=status.HTTP_400_BAD_REQUEST
        )

    items = list(panier.items.all())
    if not items:
        return Response(
            {'success': False, 'error': "Votre panier est vide."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Résoudre l'adresse de livraison
    adresse_texte = ''
    ville         = ''
    departement   = ''

    addr_id = data.get('adresse_livraison_id')
    if addr_id:
        try:
            adresse     = Adresse.objects.get(pk=addr_id, user=request.user)
            adresse_texte = adresse.rue
            ville         = adresse.commune
            departement   = adresse.departement
        except Adresse.DoesNotExist:
            return Response(
                {'success': False, 'error': "Adresse introuvable."},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        adresse_texte = data.get('adresse_livraison_text', '')
        ville         = data.get('ville_livraison', '')
        departement   = data.get('departement_livraison', '')

    # Regrouper les items par producteur
    items_par_producteur = {}
    for item in items:
        pid = item.produit.producteur.pk
        if pid not in items_par_producteur:
            items_par_producteur[pid] = {
                'producteur': item.produit.producteur,
                'items':      []
            }
        items_par_producteur[pid]['items'].append({
            'produit':  item.produit,
            'quantite': item.quantite,
        })

    commandes_creees  = []
    methode_paiement  = data['methode_paiement']
    mode_livraison    = data['mode_livraison']
    notes             = data.get('notes', '')

    # Mapper les méthodes de paiement
    METHODE_MAP = {
        'cash':       Commande.MethodePaiement.CASH,
        'moncash':    Commande.MethodePaiement.MONCASH,
        'hors_ligne': Commande.MethodePaiement.VIREMENT,
    }
    MODE_MAP = {
        'domicile': Commande.ModeLivraison.LIVRAISON_DOMICILE,
        'collecte': Commande.ModeLivraison.POINT_COLLECTE,
        'retrait':  Commande.ModeLivraison.RETRAIT_PRODUCTEUR,
    }

    methode_django = METHODE_MAP.get(methode_paiement, Commande.MethodePaiement.CASH)
    mode_django    = MODE_MAP.get(mode_livraison, Commande.ModeLivraison.LIVRAISON_DOMICILE)

    try:
        with transaction.atomic():
            for pid, groupe in items_par_producteur.items():
                commande = CommandeService.creer_commande(
                    acheteur=acheteur,
                    producteur=groupe['producteur'],
                    items=groupe['items'],
                    methode_paiement=methode_django,
                    mode_livraison=mode_django,
                    adresse_livraison=adresse_texte,
                    notes=notes,
                )
                commande.ville_livraison       = ville
                commande.departement_livraison = departement
                commande.save(update_fields=[
                    'ville_livraison', 'departement_livraison'
                ])

                # Gérer la preuve hors ligne
                if methode_paiement == 'hors_ligne':
                    preuve = data.get('preuve_paiement')
                    if preuve:
                        commande.preuve_paiement  = preuve
                        commande.statut_paiement  = Commande.StatutPaiement.PREUVE_SOUMISE
                        commande.save(update_fields=[
                            'preuve_paiement', 'statut_paiement'
                        ])

                commandes_creees.append(commande)

            # Vider le panier après commande réussie
            panier.items.all().delete()

    except ValueError as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Construire la réponse
    response_commandes = [
        {
            'numero_commande': c.numero_commande,
            'producteur':      c.producteur.user.get_full_name(),
            'total':           str(c.total),
            'statut':          c.get_statut_display(),
        }
        for c in commandes_creees
    ]

    response_data = {
        'message':   f"{len(commandes_creees)} commande(s) créée(s) avec succès !",
        'commandes': response_commandes,
    }

    # Pour MonCash — initier le paiement et retourner le redirect_url
    if methode_paiement == 'moncash' and commandes_creees:
        try:
            premiere_commande = commandes_creees[0]
            moncash = MonCashService()
            result  = moncash.initier_paiement(
                commande_id=premiere_commande.pk,
                montant_htg=premiere_commande.total
            )
            response_data['redirect_url']    = result['redirect_url']
            response_data['moncash_token']   = result['token']
        except Exception as e:
            # MonCash indisponible — commandes créées mais paiement à faire manuellement
            response_data['moncash_erreur'] = (
                "Paiement MonCash temporairement indisponible. "
                "Vos commandes ont été créées. Contactez-nous."
            )

    return Response(
        {'success': True, 'data': response_data},
        status=status.HTTP_201_CREATED
    )
```

---

### `apps/orders/views/__init__.py`

```python
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
```

---

## ÉTAPE 11 — URLs Orders

### `apps/orders/urls.py` ← REMPLACER le fichier vide

```python
from django.urls import path
from apps.orders import views

app_name = 'orders'

urlpatterns = [
    # Panier
    path('panier/',                         views.panier_resume,  name='panier_resume'),
    path('panier/ajouter/',                 views.panier_ajouter, name='panier_ajouter'),
    path('panier/modifier/<slug:slug>/',    views.panier_modifier,name='panier_modifier'),
    path('panier/retirer/<slug:slug>/',     views.panier_retirer, name='panier_retirer'),
    path('panier/vider/',                   views.panier_vider,   name='panier_vider'),

    # Commander
    path('commander/',                      views.commander,      name='commander'),
]
```

---

## ÉTAPE 12 — Migrations et vérification

```bash
# 1. Créer la migration pour le modèle Panier
python manage.py makemigrations orders --settings=config.settings.development

# 2. Appliquer
python manage.py migrate --settings=config.settings.development

# 3. Vérifier
python manage.py check --settings=config.settings.development

# 4. Lancer le serveur
python manage.py runserver --settings=config.settings.development
```

---

## ÉTAPE 13 — Tests rapides curl

```bash
BASE="http://localhost:8000"
TOKEN="<ton_access_token>"

# Liste produits
curl "$BASE/api/products/"

# Liste avec filtres
curl "$BASE/api/products/?categorie=legumes&departement=ouest"

# Recherche
curl "$BASE/api/products/?search=banane"

# Détail produit
curl "$BASE/api/products/public/banane-ti-malice/"

# Catégories
curl "$BASE/api/products/categories/"

# Panier — résumé
curl "$BASE/api/orders/panier/" \
  -H "Authorization: Bearer $TOKEN"

# Ajouter au panier
curl -X POST "$BASE/api/orders/panier/ajouter/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slug": "banane-ti-malice", "quantite": 2}'

# Modifier quantité
curl -X PATCH "$BASE/api/orders/panier/modifier/banane-ti-malice/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quantite": 3}'

# Passer commande (cash)
curl -X POST "$BASE/api/orders/commander/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "methode_paiement": "cash",
    "mode_livraison": "domicile",
    "adresse_livraison_text": "Rue des Mangues",
    "ville_livraison": "Pétion-Ville",
    "departement_livraison": "ouest",
    "notes": "Livrer le matin SVP"
  }'
```

---

## RÉSUMÉ — Endpoints créés dans ce prompt

### Catalogue public
| Méthode | Endpoint | Auth |
|---------|----------|------|
| GET | `/api/products/` | Public |
| GET | `/api/products/categories/` | Public |
| GET | `/api/products/public/<slug>/` | Public |

### Mes Produits (Producteur)
| Méthode | Endpoint | Auth |
|---------|----------|------|
| GET/POST | `/api/products/mes-produits/` | Producteur |
| GET/PATCH/DELETE | `/api/products/mes-produits/<slug>/` | Producteur |

### Panier
| Méthode | Endpoint | Auth |
|---------|----------|------|
| GET | `/api/orders/panier/` | Requis |
| POST | `/api/orders/panier/ajouter/` | Requis |
| PATCH | `/api/orders/panier/modifier/<slug>/` | Requis |
| DELETE | `/api/orders/panier/retirer/<slug>/` | Requis |
| DELETE | `/api/orders/panier/vider/` | Requis |

### Commander
| Méthode | Endpoint | Auth |
|---------|----------|------|
| POST | `/api/orders/commander/` | Acheteur |
