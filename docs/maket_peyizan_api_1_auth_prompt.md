# PROMPT CLAUDE CODE — Makèt Peyizan
# API REST — Partie 1 : Auth, Adresses, Dashboard Producteur

---

## CONTEXTE

Tu travailles sur **Makèt Peyizan** (marketplace agricole haïtienne).
Le backend Django est déjà en place avec tous les modèles.
Tu vas maintenant implémenter l'**API REST** pour l'application mobile Flutter.

**Stack API :**
- Django REST Framework (DRF)
- JWT via `djangorestframework-simplejwt`
- `drf-spectacular` pour la documentation OpenAPI

**Règles importantes :**
- Toutes les réponses JSON suivent ce format de succès :
  `{ "success": true, "data": {...} }`
- Toutes les erreurs suivent :
  `{ "success": false, "error": "message" }`
- Les endpoints protégés nécessitent `Authorization: Bearer <access_token>`

---

## FICHIERS À CRÉER

```
apps/accounts/
├── serializers/
│   ├── __init__.py
│   ├── auth_serializers.py
│   ├── adresse_serializers.py
│   └── producteur_serializers.py
├── views/
│   ├── __init__.py
│   ├── auth_views.py
│   ├── adresse_views.py
│   └── producteur_views.py
├── permissions.py
└── urls.py          ← remplacer le fichier vide existant

apps/accounts/models/
└── adresse.py       ← nouveau modèle à créer
```

---

## ÉTAPE 1 — Modèle Adresse (à créer)

### `apps/accounts/models/adresse.py`

```python
from django.db import models
from django.conf import settings


class Adresse(models.Model):
    """
    Adresse de livraison d'un utilisateur.
    """
    user                = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                            related_name='adresses'
                          )
    rue                 = models.CharField(max_length=200)
    commune             = models.CharField(max_length=100)
    departement         = models.CharField(max_length=50)
    section_communale   = models.CharField(max_length=100, blank=True)
    telephone           = models.CharField(max_length=20, blank=True)
    instructions        = models.TextField(blank=True)
    is_default          = models.BooleanField(default=False)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Adresse'
        verbose_name_plural = 'Adresses'
        ordering            = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.rue}, {self.commune} ({self.user.get_full_name()})"

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule adresse par défaut
        if self.is_default:
            Adresse.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
```

### Mettre à jour `apps/accounts/models/__init__.py`

```python
from .user       import CustomUser
from .producteur import Producteur
from .acheteur   import Acheteur
from .adresse    import Adresse

__all__ = ['CustomUser', 'Producteur', 'Acheteur', 'Adresse']
```

---

## ÉTAPE 2 — Permissions personnalisées

### `apps/accounts/permissions.py`

```python
from rest_framework.permissions import BasePermission


class IsProducteur(BasePermission):
    """Autorise uniquement les utilisateurs avec le rôle producteur."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'producteur'
        )


class IsAcheteur(BasePermission):
    """Autorise uniquement les acheteurs."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'acheteur'
        )


class IsProducteurActif(BasePermission):
    """Autorise uniquement les producteurs avec statut actif."""
    message = "Votre compte producteur est en attente de validation."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role != 'producteur':
            return False
        try:
            return request.user.profil_producteur.statut == 'actif'
        except Exception:
            return False


class IsSuperAdmin(BasePermission):
    """Autorise uniquement les superadmins."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (
                request.user.is_superuser or
                request.user.is_staff or
                request.user.role == 'superadmin'
            )
        )
```

---

## ÉTAPE 3 — Serializers Auth

### `apps/accounts/serializers/auth_serializers.py`

```python
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    """Inscription d'un nouvel utilisateur."""
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta:
        model  = CustomUser
        fields = [
            'username', 'email', 'password', 'role',
            'first_name', 'last_name', 'telephone'
        ]
        extra_kwargs = {
            'email':      {'required': True},
            'first_name': {'required': True},
            'last_name':  {'required': True},
        }

    def validate_role(self, value):
        allowed = ['acheteur', 'producteur', 'collecteur']
        if value not in allowed:
            raise serializers.ValidationError(
                f"Rôle invalide. Valeurs acceptées : {', '.join(allowed)}"
            )
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Un compte avec cet email existe déjà."
            )
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username   = validated_data['username'],
            email      = validated_data['email'],
            password   = validated_data['password'],
            role       = validated_data.get('role', 'acheteur'),
            first_name = validated_data.get('first_name', ''),
            last_name  = validated_data.get('last_name', ''),
            telephone  = validated_data.get('telephone', ''),
        )

        # Créer le profil associé selon le rôle
        if user.role == 'producteur':
            from apps.accounts.models import Producteur
            Producteur.objects.create(
                user=user,
                statut='en_attente'
            )
        elif user.role == 'acheteur':
            from apps.accounts.models import Acheteur
            Acheteur.objects.create(user=user)

        return user


class LoginSerializer(serializers.Serializer):
    """Connexion par email + mot de passe."""
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email    = data.get('email')
        password = data.get('password')

        # Trouver l'utilisateur par email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                "Email ou mot de passe incorrect."
            )

        # Vérifier le mot de passe
        user = authenticate(username=user.username, password=password)
        if not user:
            raise serializers.ValidationError(
                "Email ou mot de passe incorrect."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "Ce compte est désactivé."
            )

        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Profil de l'utilisateur connecté."""
    profil_producteur_statut = serializers.SerializerMethodField()

    class Meta:
        model  = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'telephone', 'photo', 'role', 'is_verified',
            'is_superuser', 'is_staff',
            'profil_producteur_statut', 'created_at'
        ]
        read_only_fields = [
            'id', 'username', 'role', 'is_verified',
            'is_superuser', 'is_staff', 'created_at'
        ]

    def get_profil_producteur_statut(self, obj):
        if obj.role == 'producteur':
            try:
                return obj.profil_producteur.statut
            except Exception:
                return None
        return None


class ChangePasswordSerializer(serializers.Serializer):
    """Changement de mot de passe."""
    current_password = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Mot de passe actuel incorrect."
            )
        return value


class FCMTokenSerializer(serializers.Serializer):
    """Enregistrement du token Firebase."""
    fcm_token = serializers.CharField()
```

---

## ÉTAPE 4 — Serializers Adresse

### `apps/accounts/serializers/adresse_serializers.py`

```python
from rest_framework import serializers
from apps.accounts.models import Adresse


class AdresseSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Adresse
        fields = [
            'id', 'rue', 'commune', 'departement',
            'section_communale', 'telephone',
            'instructions', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
```

---

## ÉTAPE 5 — Serializers Producteur

### `apps/accounts/serializers/producteur_serializers.py`

```python
from rest_framework import serializers
from apps.accounts.models import Producteur
from apps.orders.models import Commande


class ProducteurProfilSerializer(serializers.ModelSerializer):
    """Profil public/privé d'un producteur."""
    nom_complet  = serializers.SerializerMethodField()
    email        = serializers.SerializerMethodField()
    telephone    = serializers.SerializerMethodField()
    photo        = serializers.SerializerMethodField()
    nb_produits  = serializers.SerializerMethodField()
    nb_commandes = serializers.SerializerMethodField()

    class Meta:
        model  = Producteur
        fields = [
            'id', 'code_producteur', 'nom_complet', 'email',
            'telephone', 'photo', 'departement', 'commune',
            'localite', 'adresse_complete', 'superficie_ha',
            'description', 'statut', 'nb_produits', 'nb_commandes',
            'created_at'
        ]
        read_only_fields = [
            'id', 'code_producteur', 'statut', 'created_at'
        ]

    def get_nom_complet(self, obj):
        return obj.user.get_full_name()

    def get_email(self, obj):
        return obj.user.email

    def get_telephone(self, obj):
        return obj.user.telephone

    def get_photo(self, obj):
        if obj.user.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.photo.url)
        return None

    def get_nb_produits(self, obj):
        return obj.nb_produits_actifs

    def get_nb_commandes(self, obj):
        return obj.nb_commandes_total


class ProducteurStatsSerializer(serializers.Serializer):
    """Statistiques du dashboard producteur."""
    commandes_en_attente    = serializers.IntegerField()
    commandes_confirmees    = serializers.IntegerField()
    commandes_livrees       = serializers.IntegerField()
    commandes_total         = serializers.IntegerField()
    revenus_total           = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenus_mois            = serializers.DecimalField(max_digits=12, decimal_places=2)
    nb_produits_actifs      = serializers.IntegerField()
    nb_produits_epuises     = serializers.IntegerField()
    alertes_stock           = serializers.IntegerField()
    collectes_a_venir       = serializers.IntegerField()


class CommandeProducteurSerializer(serializers.ModelSerializer):
    """Commande vue depuis le dashboard producteur."""
    acheteur_nom   = serializers.SerializerMethodField()
    acheteur_tel   = serializers.SerializerMethodField()
    acheteur_type  = serializers.SerializerMethodField()
    statut_label   = serializers.CharField(
                       source='get_statut_display', read_only=True
                     )
    paiement_label = serializers.CharField(
                       source='get_statut_paiement_display', read_only=True
                     )
    details        = serializers.SerializerMethodField()

    class Meta:
        model  = Commande
        fields = [
            'numero_commande', 'acheteur_nom', 'acheteur_tel',
            'acheteur_type', 'sous_total', 'frais_livraison',
            'remise', 'total', 'statut', 'statut_label',
            'statut_paiement', 'paiement_label',
            'methode_paiement', 'mode_livraison',
            'adresse_livraison', 'notes_acheteur',
            'date_confirmation', 'created_at', 'details'
        ]

    def get_acheteur_nom(self, obj):
        return obj.acheteur.user.get_full_name()

    def get_acheteur_tel(self, obj):
        return obj.acheteur.user.telephone

    def get_acheteur_type(self, obj):
        return obj.acheteur.get_type_acheteur_display()

    def get_details(self, obj):
        return [
            {
                'produit':       d.produit.nom,
                'slug':          d.produit.slug,
                'quantite':      d.quantite,
                'unite_vente':   d.unite_vente,
                'prix_unitaire': str(d.prix_unitaire),
                'sous_total':    str(d.sous_total),
            }
            for d in obj.details.select_related('produit').all()
        ]
```

---

## ÉTAPE 6 — `apps/accounts/serializers/__init__.py`

```python
from .auth_serializers      import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    FCMTokenSerializer,
)
from .adresse_serializers    import AdresseSerializer
from .producteur_serializers import (
    ProducteurProfilSerializer,
    ProducteurStatsSerializer,
    CommandeProducteurSerializer,
)

__all__ = [
    'RegisterSerializer', 'LoginSerializer', 'UserProfileSerializer',
    'ChangePasswordSerializer', 'FCMTokenSerializer',
    'AdresseSerializer',
    'ProducteurProfilSerializer', 'ProducteurStatsSerializer',
    'CommandeProducteurSerializer',
]
```

---

## ÉTAPE 7 — Vues Auth

### `apps/accounts/views/auth_views.py`

```python
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.accounts.models import CustomUser
from apps.accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    FCMTokenSerializer,
)


def _get_tokens(user):
    """Génère les tokens JWT pour un utilisateur."""
    refresh = RefreshToken.for_user(user)
    return {
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
    }


def _user_data(user, request=None):
    """Retourne les données utilisateur sérialisées."""
    return UserProfileSerializer(user, context={'request': request}).data


# ── POST /api/auth/register/ ────────────────────────────────────
@extend_schema(tags=['Auth'], summary='Inscription')
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    user   = serializer.save()
    tokens = _get_tokens(user)

    return Response(
        {
            'success': True,
            'data': {
                **tokens,
                'user': _user_data(user, request),
            }
        },
        status=status.HTTP_201_CREATED
    )


# ── POST /api/auth/login/ ───────────────────────────────────────
@extend_schema(tags=['Auth'], summary='Connexion')
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    user   = serializer.validated_data['user']
    tokens = _get_tokens(user)

    return Response(
        {
            'success': True,
            'data': {
                **tokens,
                'user': _user_data(user, request),
            }
        }
    )


# ── POST /api/auth/logout/ ──────────────────────────────────────
@extend_schema(tags=['Auth'], summary='Déconnexion')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get('refresh')
    fcm_token     = request.data.get('fcm_token')

    # Blacklister le refresh token
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass

    # Supprimer le FCM token
    if fcm_token and request.user.fcm_token == fcm_token:
        request.user.fcm_token = ''
        request.user.save(update_fields=['fcm_token'])

    return Response({'success': True, 'data': {'message': 'Déconnexion réussie.'}})


# ── POST /api/auth/token/refresh/ ──────────────────────────────
# Géré nativement par simplejwt — voir urls.py


# ── GET/PATCH /api/auth/me/ ─────────────────────────────────────
@extend_schema(tags=['Auth'], summary='Profil utilisateur')
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == 'GET':
        return Response({
            'success': True,
            'data': _user_data(request.user, request)
        })

    # PATCH — mise à jour partielle (multipart pour photo)
    serializer = UserProfileSerializer(
        request.user,
        data=request.data,
        partial=True,
        context={'request': request}
    )
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer.save()
    return Response({
        'success': True,
        'data': _user_data(request.user, request)
    })


# ── POST /api/auth/change-password/ ────────────────────────────
@extend_schema(tags=['Auth'], summary='Changer le mot de passe')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save()
    return Response({
        'success': True,
        'data': {'message': 'Mot de passe modifié avec succès.'}
    })


# ── POST /api/auth/fcm-token/ ───────────────────────────────────
@extend_schema(tags=['Auth'], summary='Enregistrer token FCM')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fcm_token(request):
    serializer = FCMTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    token = serializer.validated_data['fcm_token']
    request.user.fcm_token = token
    request.user.save(update_fields=['fcm_token'])

    # Abonner au topic FCM selon le rôle
    topic = f"role_{request.user.role}"

    return Response({
        'success': True,
        'data': {
            'message':         'Token enregistré.',
            'role':            request.user.role,
            'topic_subscribed': topic,
        }
    })
```

---

## ÉTAPE 8 — Vues Adresses

### `apps/accounts/views/adresse_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.models import Adresse
from apps.accounts.serializers import AdresseSerializer


# ── GET/POST /api/auth/adresses/ ────────────────────────────────
@extend_schema(tags=['Adresses'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def adresses_list(request):
    if request.method == 'GET':
        adresses   = Adresse.objects.filter(user=request.user)
        serializer = AdresseSerializer(adresses, many=True)
        return Response({'success': True, 'data': serializer.data})

    # POST — créer une adresse
    serializer = AdresseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    adresse = serializer.save(user=request.user)
    return Response(
        {'success': True, 'data': AdresseSerializer(adresse).data},
        status=status.HTTP_201_CREATED
    )


# ── GET/PUT/PATCH/DELETE /api/auth/adresses/<id>/ ───────────────
@extend_schema(tags=['Adresses'])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def adresse_detail(request, pk):
    adresse = get_object_or_404(Adresse, pk=pk, user=request.user)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': AdresseSerializer(adresse).data
        })

    if request.method in ['PUT', 'PATCH']:
        serializer = AdresseSerializer(
            adresse,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response({'success': True, 'data': serializer.data})

    # DELETE
    adresse.delete()
    return Response(
        {'success': True, 'data': {'message': 'Adresse supprimée.'}},
        status=status.HTTP_200_OK
    )


# ── PATCH /api/auth/adresses/<id>/default/ ──────────────────────
@extend_schema(tags=['Adresses'])
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def adresse_set_default(request, pk):
    adresse             = get_object_or_404(Adresse, pk=pk, user=request.user)
    adresse.is_default  = True
    adresse.save()
    return Response({
        'success': True,
        'data': {
            'message': 'Adresse définie comme adresse par défaut.',
            'adresse': AdresseSerializer(adresse).data
        }
    })
```

---

## ÉTAPE 9 — Vues Dashboard Producteur

### `apps/accounts/views/producteur_views.py`

```python
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsProducteur
from apps.accounts.serializers import (
    ProducteurProfilSerializer,
    ProducteurStatsSerializer,
    CommandeProducteurSerializer,
)
from apps.orders.models import Commande
from apps.orders.services.commande_service import CommandeService
from apps.stock.models import AlerteStock
from apps.collectes.models import Collecte


# ── GET /api/auth/producteur/stats/ ────────────────────────────
@extend_schema(tags=['Producteur'])
@api_view(['GET'])
@permission_classes([IsProducteur])
def producteur_stats(request):
    producteur = request.user.profil_producteur
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0)

    commandes_qs = Commande.objects.filter(producteur=producteur)

    # Revenus
    revenus_total = commandes_qs.filter(
        statut__in=['confirmee', 'en_preparation', 'prete', 'en_collecte', 'livree'],
        statut_paiement='paye'
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    revenus_mois = commandes_qs.filter(
        statut__in=['confirmee', 'livree'],
        statut_paiement='paye',
        created_at__gte=debut_mois
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    # Alertes stock actives
    alertes = AlerteStock.objects.filter(
        produit__producteur=producteur,
        statut__in=['nouvelle', 'vue']
    ).count()

    # Collectes à venir
    collectes_a_venir = Collecte.objects.filter(
        participations__producteur=producteur,
        statut='planifiee',
        date_prevue__gte=timezone.now().date()
    ).count()

    stats = {
        'commandes_en_attente':  commandes_qs.filter(statut='en_attente').count(),
        'commandes_confirmees':  commandes_qs.filter(statut='confirmee').count(),
        'commandes_livrees':     commandes_qs.filter(statut='livree').count(),
        'commandes_total':       commandes_qs.count(),
        'revenus_total':         revenus_total,
        'revenus_mois':          revenus_mois,
        'nb_produits_actifs':    producteur.nb_produits_actifs,
        'nb_produits_epuises':   producteur.produits.filter(statut='epuise').count(),
        'alertes_stock':         alertes,
        'collectes_a_venir':     collectes_a_venir,
    }

    serializer = ProducteurStatsSerializer(stats)
    return Response({'success': True, 'data': serializer.data})


# ── GET/PATCH /api/auth/producteur/profil/ ─────────────────────
@extend_schema(tags=['Producteur'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsProducteur])
def producteur_profil(request):
    producteur = request.user.profil_producteur

    if request.method == 'GET':
        serializer = ProducteurProfilSerializer(
            producteur, context={'request': request}
        )
        return Response({'success': True, 'data': serializer.data})

    # PATCH — modifier profil boutique
    serializer = ProducteurProfilSerializer(
        producteur,
        data=request.data,
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


# ── GET /api/auth/producteur/commandes/ ─────────────────────────
@extend_schema(tags=['Producteur'])
@api_view(['GET'])
@permission_classes([IsProducteur])
def producteur_commandes(request):
    producteur = request.user.profil_producteur
    statut     = request.query_params.get('statut', '')

    qs = Commande.objects.filter(
        producteur=producteur
    ).select_related(
        'acheteur__user'
    ).prefetch_related('details__produit')

    if statut:
        qs = qs.filter(statut=statut)

    qs = qs.order_by('-created_at')

    serializer = CommandeProducteurSerializer(qs, many=True)
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/auth/producteur/commandes/<numero>/ ─────────────────
@extend_schema(tags=['Producteur'])
@api_view(['GET'])
@permission_classes([IsProducteur])
def producteur_commande_detail(request, numero):
    producteur = request.user.profil_producteur
    commande   = get_object_or_404(
        Commande,
        numero_commande=numero,
        producteur=producteur
    )
    serializer = CommandeProducteurSerializer(commande)
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/auth/producteur/commandes/<numero>/statut/ ────────
@extend_schema(tags=['Producteur'])
@api_view(['PATCH'])
@permission_classes([IsProducteur])
def producteur_commande_statut(request, numero):
    producteur = request.user.profil_producteur
    commande   = get_object_or_404(
        Commande,
        numero_commande=numero,
        producteur=producteur
    )

    action = request.data.get('action')
    motif  = request.data.get('motif', '')

    TRANSITIONS = {
        'confirmer': (
            [Commande.Statut.EN_ATTENTE],
            Commande.Statut.CONFIRMEE
        ),
        'preparer': (
            [Commande.Statut.CONFIRMEE],
            Commande.Statut.EN_PREPARATION
        ),
        'prete': (
            [Commande.Statut.EN_PREPARATION],
            Commande.Statut.PRETE
        ),
        'annuler': (
            [
                Commande.Statut.EN_ATTENTE,
                Commande.Statut.CONFIRMEE,
                Commande.Statut.EN_PREPARATION,
            ],
            Commande.Statut.ANNULEE
        ),
    }

    if action not in TRANSITIONS:
        return Response(
            {'success': False, 'error': f"Action invalide. Valeurs : {list(TRANSITIONS.keys())}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    statuts_autorisés, nouveau_statut = TRANSITIONS[action]

    if commande.statut not in statuts_autorisés:
        return Response(
            {
                'success': False,
                'error': (
                    f"Impossible de '{action}' une commande "
                    f"avec le statut '{commande.get_statut_display()}'."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if action == 'annuler' and not motif:
        return Response(
            {'success': False, 'error': "Le motif est requis pour annuler une commande."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if action == 'confirmer':
            CommandeService.confirmer_commande(commande, request.user)
        elif action == 'annuler':
            CommandeService.annuler_commande(commande, request.user, motif)
        else:
            CommandeService.changer_statut(
                commande, nouveau_statut,
                effectue_par=request.user
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
            'message':         f"Commande {action}e avec succès."
        }
    })
```

---

## ÉTAPE 10 — `apps/accounts/views/__init__.py`

```python
from .auth_views       import register, login, logout, me, change_password, fcm_token
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
    'adresses_list', 'adresse_detail', 'adresse_set_default',
    'producteur_stats', 'producteur_profil',
    'producteur_commandes', 'producteur_commande_detail',
    'producteur_commande_statut',
]
```

---

## ÉTAPE 11 — URLs complètes

### `apps/accounts/urls.py` ← REMPLACER le fichier vide

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [

    # ── Auth ────────────────────────────────────────────────────
    path('register/',         views.register,         name='register'),
    path('login/',            views.login,            name='login'),
    path('logout/',           views.logout,           name='logout'),
    path('token/refresh/',    TokenRefreshView.as_view(), name='token_refresh'),
    path('me/',               views.me,               name='me'),
    path('change-password/',  views.change_password,  name='change_password'),
    path('fcm-token/',        views.fcm_token,        name='fcm_token'),

    # ── Adresses ────────────────────────────────────────────────
    path('adresses/',                      views.adresses_list,    name='adresses_list'),
    path('adresses/<int:pk>/',             views.adresse_detail,   name='adresse_detail'),
    path('adresses/<int:pk>/default/',     views.adresse_set_default, name='adresse_default'),

    # ── Dashboard Producteur ────────────────────────────────────
    path('producteur/stats/',              views.producteur_stats,             name='producteur_stats'),
    path('producteur/profil/',             views.producteur_profil,            name='producteur_profil'),
    path('producteur/commandes/',          views.producteur_commandes,         name='producteur_commandes'),
    path('producteur/commandes/<str:numero>/',        views.producteur_commande_detail, name='producteur_commande_detail'),
    path('producteur/commandes/<str:numero>/statut/', views.producteur_commande_statut, name='producteur_commande_statut'),
]
```

---

## ÉTAPE 12 — Commandes acheteur (sous /api/auth/commandes/)

Ajouter dans `apps/accounts/views/auth_views.py` :

```python
from apps.orders.models import Commande
from apps.accounts.serializers.producteur_serializers import CommandeProducteurSerializer


# ── GET /api/auth/commandes/ ────────────────────────────────────
@extend_schema(tags=['Acheteur'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def acheteur_commandes(request):
    """Liste des commandes de l'acheteur connecté."""
    try:
        acheteur = request.user.profil_acheteur
    except Exception:
        return Response(
            {'success': False, 'error': 'Profil acheteur introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )

    commandes = Commande.objects.filter(
        acheteur=acheteur
    ).select_related('producteur__user').order_by('-created_at')

    data = [
        {
            'numero_commande': c.numero_commande,
            'producteur':      c.producteur.user.get_full_name(),
            'total':           str(c.total),
            'statut':          c.statut,
            'statut_label':    c.get_statut_display(),
            'statut_paiement': c.statut_paiement,
            'created_at':      c.created_at.isoformat(),
        }
        for c in commandes
    ]
    return Response({'success': True, 'data': data})


# ── GET /api/auth/commandes/<numero>/ ───────────────────────────
@extend_schema(tags=['Acheteur'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def acheteur_commande_detail(request, numero):
    """Détail d'une commande acheteur."""
    try:
        acheteur = request.user.profil_acheteur
    except Exception:
        return Response(
            {'success': False, 'error': 'Profil acheteur introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )

    commande = get_object_or_404(
        Commande,
        numero_commande=numero,
        acheteur=acheteur
    )
    serializer = CommandeProducteurSerializer(commande)
    return Response({'success': True, 'data': serializer.data})
```

Ajouter dans `apps/accounts/urls.py` :
```python
path('commandes/',                views.acheteur_commandes,       name='acheteur_commandes'),
path('commandes/<str:numero>/',   views.acheteur_commande_detail, name='acheteur_commande_detail'),
```

Et dans `apps/accounts/views/__init__.py` :
```python
from .auth_views import ..., acheteur_commandes, acheteur_commande_detail
```

---

## ÉTAPE 13 — Migration et vérification

```bash
# 1. Créer la migration pour le modèle Adresse
python manage.py makemigrations accounts --settings=config.settings.development

# 2. Appliquer les migrations
python manage.py migrate --settings=config.settings.development

# 3. Vérifier qu'il n'y a pas d'erreur
python manage.py check --settings=config.settings.development

# 4. Lancer le serveur
python manage.py runserver --settings=config.settings.development

# 5. Tester dans Swagger
# http://localhost:8000/api/schema/swagger-ui/
```

---

## ÉTAPE 14 — Tests rapides avec curl

```bash
BASE="http://localhost:8000"

# Inscription acheteur
curl -X POST $BASE/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_acheteur",
    "email": "acheteur@test.com",
    "password": "Test1234!",
    "role": "acheteur",
    "first_name": "Jean",
    "last_name": "Dupont",
    "telephone": "+50912345678"
  }'

# Inscription producteur
curl -X POST $BASE/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_producteur",
    "email": "producteur@test.com",
    "password": "Test1234!",
    "role": "producteur",
    "first_name": "Marie",
    "last_name": "Joseph"
  }'

# Login
curl -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "acheteur@test.com", "password": "Test1234!"}'

# Profil (remplacer TOKEN)
curl $BASE/api/auth/me/ \
  -H "Authorization: Bearer TOKEN"

# Créer une adresse
curl -X POST $BASE/api/auth/adresses/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rue": "Rue des Mangues",
    "commune": "Pétion-Ville",
    "departement": "ouest",
    "section_communale": "1ère section",
    "telephone": "+50912345678"
  }'
```

---

## RÉSUMÉ — Endpoints créés dans ce prompt

### Auth
| Méthode | Endpoint | Auth |
|---------|----------|------|
| POST | `/api/auth/register/` | Public |
| POST | `/api/auth/login/` | Public |
| POST | `/api/auth/logout/` | Requis |
| POST | `/api/auth/token/refresh/` | Public |
| GET/PATCH | `/api/auth/me/` | Requis |
| POST | `/api/auth/change-password/` | Requis |
| POST | `/api/auth/fcm-token/` | Requis |

### Adresses
| Méthode | Endpoint | Auth |
|---------|----------|------|
| GET/POST | `/api/auth/adresses/` | Requis |
| GET/PUT/PATCH/DELETE | `/api/auth/adresses/<id>/` | Requis |
| PATCH | `/api/auth/adresses/<id>/default/` | Requis |

### Commandes Acheteur
| Méthode | Endpoint | Auth |
|---------|----------|------|
| GET | `/api/auth/commandes/` | Requis |
| GET | `/api/auth/commandes/<numero>/` | Requis |

### Dashboard Producteur
| Méthode | Endpoint | Auth |
|---------|----------|------|
| GET | `/api/auth/producteur/stats/` | Producteur |
| GET/PATCH | `/api/auth/producteur/profil/` | Producteur |
| GET | `/api/auth/producteur/commandes/` | Producteur |
| GET | `/api/auth/producteur/commandes/<numero>/` | Producteur |
| PATCH | `/api/auth/producteur/commandes/<numero>/statut/` | Producteur |
