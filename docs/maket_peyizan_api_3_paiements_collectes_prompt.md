# PROMPT CLAUDE CODE — Makèt Peyizan
# API REST — Partie 3 : Paiements & Collectes

---

## CONTEXTE

Tu travailles sur **Makèt Peyizan** (marketplace agricole haïtienne).
Les Parties 1 et 2 sont déjà implémentées et fonctionnelles.

Tu vas maintenant implémenter :
- **Paiements** : initier, soumettre preuve, vérifier, voucher
- **Collectes** : participations producteur, confirmation

**Format de réponse uniforme :**
- Succès : `{ "success": true, "data": {...} }`
- Erreur  : `{ "success": false, "error": "message" }`

---

## FICHIERS À CRÉER

```
apps/payments/
├── serializers/
│   ├── __init__.py
│   ├── paiement_serializers.py
│   └── voucher_serializers.py
├── views/
│   ├── __init__.py
│   ├── paiement_views.py
│   └── voucher_views.py
└── urls.py          ← remplacer le fichier vide

apps/collectes/
├── serializers/
│   ├── __init__.py
│   └── collecte_serializers.py
├── views/
│   ├── __init__.py
│   └── collecte_views.py
└── urls.py          ← remplacer le fichier vide
```

---

## ÉTAPE 1 — Serializers Paiements

### `apps/payments/serializers/paiement_serializers.py`

```python
from rest_framework import serializers
from apps.payments.models import Paiement
from apps.orders.models import Commande


class InitierPaiementSerializer(serializers.Serializer):
    """Données pour initier un paiement."""
    commande_numero    = serializers.CharField()
    type_paiement      = serializers.ChoiceField(
                           choices=['moncash', 'natcash', 'virement', 'cash']
                         )
    numero_expediteur  = serializers.CharField(
                           required=False, allow_blank=True,
                           help_text="Numéro MonCash/NatCash expéditeur"
                         )
    notes              = serializers.CharField(
                           required=False, allow_blank=True
                         )

    def validate_commande_numero(self, value):
        try:
            return Commande.objects.get(numero_commande=value)
        except Commande.DoesNotExist:
            raise serializers.ValidationError(
                f"Commande '{value}' introuvable."
            )


class SoumettrePreuveSerializer(serializers.Serializer):
    """Données pour soumettre une preuve de paiement."""
    paiement_id    = serializers.IntegerField()
    preuve_image   = serializers.ImageField()
    id_transaction = serializers.CharField(
                       required=False, allow_blank=True
                     )
    montant_recu   = serializers.DecimalField(
                       max_digits=12, decimal_places=2,
                       required=False, allow_null=True
                     )


class VerifierPaiementSerializer(serializers.Serializer):
    """Vérifier le statut d'un paiement."""
    paiement_id    = serializers.IntegerField(required=False)
    id_transaction = serializers.CharField(
                       required=False, allow_blank=True
                     )

    def validate(self, data):
        if not data.get('paiement_id') and not data.get('id_transaction'):
            raise serializers.ValidationError(
                "Fournir 'paiement_id' ou 'id_transaction'."
            )
        return data


class PaiementSerializer(serializers.ModelSerializer):
    """Serializer de lecture d'un paiement."""
    type_label   = serializers.CharField(
                     source='get_type_paiement_display'
                   )
    statut_label = serializers.CharField(
                     source='get_statut_display'
                   )
    commande_numero = serializers.CharField(
                        source='commande.numero_commande'
                      )

    class Meta:
        model  = Paiement
        fields = [
            'id', 'reference', 'commande_numero',
            'type_paiement', 'type_label',
            'statut', 'statut_label',
            'montant', 'montant_recu',
            'numero_expediteur', 'id_transaction',
            'preuve_image', 'notes',
            'date_verification', 'created_at',
        ]
```

---

### `apps/payments/serializers/voucher_serializers.py`

```python
from rest_framework import serializers
from apps.payments.models import Voucher, ProgrammeVoucher


class ValiderVoucherSerializer(serializers.Serializer):
    """Valider un code voucher avant de passer commande."""
    code             = serializers.CharField(max_length=20)
    montant_commande = serializers.DecimalField(
                         max_digits=12, decimal_places=2
                       )


class VoucherSerializer(serializers.ModelSerializer):
    """Serializer de lecture d'un voucher."""
    programme_nom  = serializers.CharField(source='programme.nom')
    statut_label   = serializers.CharField(source='get_statut_display')
    type_label     = serializers.CharField(source='get_type_valeur_display')
    remise_calculee = serializers.SerializerMethodField()

    class Meta:
        model  = Voucher
        fields = [
            'code', 'programme_nom',
            'type_valeur', 'type_label',
            'valeur', 'montant_max',
            'montant_commande_min',
            'statut', 'statut_label',
            'date_expiration', 'est_valide',
            'remise_calculee',
        ]

    def get_remise_calculee(self, obj):
        montant = self.context.get('montant_commande')
        if montant:
            return str(obj.calculer_remise(montant))
        return None
```

---

### `apps/payments/serializers/__init__.py`

```python
from .paiement_serializers import (
    InitierPaiementSerializer,
    SoumettrePreuveSerializer,
    VerifierPaiementSerializer,
    PaiementSerializer,
)
from .voucher_serializers import (
    ValiderVoucherSerializer,
    VoucherSerializer,
)

__all__ = [
    'InitierPaiementSerializer',
    'SoumettrePreuveSerializer',
    'VerifierPaiementSerializer',
    'PaiementSerializer',
    'ValiderVoucherSerializer',
    'VoucherSerializer',
]
```

---

## ÉTAPE 2 — Vues Paiements

### `apps/payments/views/paiement_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.payments.models import Paiement
from apps.payments.serializers import (
    InitierPaiementSerializer,
    SoumettrePreuveSerializer,
    VerifierPaiementSerializer,
    PaiementSerializer,
)
from apps.payments.services.paiement_service import PaiementService
from apps.payments.services.moncash_service import MonCashService
from apps.orders.models import Commande


# ── POST /api/payments/initier/ ─────────────────────────────────
@extend_schema(tags=['Paiements'], summary='Initier un paiement')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initier_paiement(request):
    """
    Initier un paiement pour une commande.
    Pour MonCash/NatCash : retourne redirect_url.
    Pour cash/virement  : crée l'enregistrement et retourne la référence.
    """
    serializer = InitierPaiementSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    commande      = serializer.validated_data['commande_numero']
    type_paiement = serializer.validated_data['type_paiement']
    numero_exp    = serializer.validated_data.get('numero_expediteur', '')
    notes         = serializer.validated_data.get('notes', '')

    # Vérifier que la commande appartient à l'utilisateur
    try:
        acheteur = request.user.profil_acheteur
        if commande.acheteur != acheteur:
            return Response(
                {'success': False, 'error': "Commande non autorisée."},
                status=status.HTTP_403_FORBIDDEN
            )
    except Exception:
        return Response(
            {'success': False, 'error': "Profil acheteur requis."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Vérifier que la commande n'est pas déjà payée
    if commande.statut_paiement == Commande.StatutPaiement.PAYE:
        return Response(
            {'success': False, 'error': "Cette commande est déjà payée."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Mapper le type de paiement
    TYPE_MAP = {
        'moncash':  Paiement.TypePaiement.MONCASH,
        'natcash':  Paiement.TypePaiement.NATCASH,
        'virement': Paiement.TypePaiement.VIREMENT,
        'cash':     Paiement.TypePaiement.CASH,
    }
    type_django = TYPE_MAP.get(type_paiement, Paiement.TypePaiement.CASH)

    # Créer l'enregistrement paiement
    paiement = PaiementService.initier_paiement(
        commande=commande,
        type_paiement=type_django,
        numero_expediteur=numero_exp,
        notes=notes,
    )

    response_data = PaiementSerializer(paiement).data

    # Pour MonCash — initier via l'API et retourner le redirect
    if type_paiement == 'moncash':
        try:
            moncash = MonCashService()
            result  = moncash.initier_paiement(
                commande_id=commande.pk,
                montant_htg=commande.total
            )
            response_data['redirect_url']  = result['redirect_url']
            response_data['moncash_token'] = result['token']
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': f"Service MonCash indisponible : {str(e)}"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    return Response(
        {'success': True, 'data': response_data},
        status=status.HTTP_201_CREATED
    )


# ── POST /api/payments/preuve/ ──────────────────────────────────
@extend_schema(tags=['Paiements'], summary='Soumettre une preuve de paiement')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def soumettre_preuve(request):
    """
    Soumettre une preuve de paiement (image JPG/PNG, max 5MB).
    Utilisé pour les paiements hors ligne / virement.
    Content-Type: multipart/form-data
    """
    serializer = SoumettrePreuveSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    paiement_id  = serializer.validated_data['paiement_id']
    preuve       = serializer.validated_data['preuve_image']
    id_trans     = serializer.validated_data.get('id_transaction', '')
    montant_recu = serializer.validated_data.get('montant_recu')

    # Récupérer le paiement
    try:
        paiement = Paiement.objects.select_related(
            'commande__acheteur__user'
        ).get(pk=paiement_id)
    except Paiement.DoesNotExist:
        return Response(
            {'success': False, 'error': "Paiement introuvable."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Vérifier que le paiement appartient à l'utilisateur
    if paiement.commande.acheteur.user != request.user:
        return Response(
            {'success': False, 'error': "Paiement non autorisé."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Vérifier le statut
    if paiement.statut not in [
        Paiement.Statut.INITIE,
        Paiement.Statut.EN_ATTENTE
    ]:
        return Response(
            {
                'success': False,
                'error': (
                    "Ce paiement ne peut plus recevoir de preuve "
                    f"(statut actuel : {paiement.get_statut_display()})."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Soumettre la preuve
    paiement = PaiementService.soumettre_preuve(
        paiement=paiement,
        preuve_image=preuve,
        id_transaction=id_trans,
        montant_recu=montant_recu,
    )

    return Response({
        'success': True,
        'data': {
            **PaiementSerializer(paiement).data,
            'message': (
                "Preuve de paiement reçue. "
                "L'admin va vérifier et confirmer votre commande."
            ),
        }
    })


# ── POST /api/payments/verifier/ ────────────────────────────────
@extend_schema(tags=['Paiements'], summary='Vérifier le statut d\'un paiement')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verifier_paiement(request):
    """
    Vérifier le statut d'un paiement.
    Optionnel : vérification MonCash via l'API si id_transaction fourni.
    """
    serializer = VerifierPaiementSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    paiement_id   = serializer.validated_data.get('paiement_id')
    id_transaction = serializer.validated_data.get('id_transaction')

    # Récupérer le paiement
    if paiement_id:
        paiement = get_object_or_404(Paiement, pk=paiement_id)
    else:
        paiement = get_object_or_404(
            Paiement, id_transaction=id_transaction
        )

    # Vérifier l'appartenance
    if (
        paiement.commande.acheteur.user != request.user and
        not request.user.is_staff
    ):
        return Response(
            {'success': False, 'error': "Paiement non autorisé."},
            status=status.HTTP_403_FORBIDDEN
        )

    response_data = PaiementSerializer(paiement).data

    # Pour MonCash — vérifier via l'API si non encore confirmé
    if (
        paiement.type_paiement == Paiement.TypePaiement.MONCASH and
        paiement.statut not in [Paiement.Statut.CONFIRME, Paiement.Statut.ECHOUE] and
        id_transaction
    ):
        try:
            moncash  = MonCashService()
            mc_data  = moncash.verifier_paiement(id_transaction)
            response_data['moncash_data'] = mc_data
        except Exception:
            pass

    return Response({'success': True, 'data': response_data})


# ── GET /api/payments/mes-paiements/ ────────────────────────────
@extend_schema(tags=['Paiements'], summary='Historique des paiements')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_paiements(request):
    """Historique des paiements de l'utilisateur connecté."""
    try:
        acheteur  = request.user.profil_acheteur
        paiements = Paiement.objects.filter(
            commande__acheteur=acheteur
        ).select_related('commande').order_by('-created_at')
    except Exception:
        paiements = Paiement.objects.none()

    serializer = PaiementSerializer(paiements, many=True)
    return Response({'success': True, 'data': serializer.data})
```

---

## ÉTAPE 3 — Vues Vouchers

### `apps/payments/views/voucher_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.payments.models import Voucher
from apps.payments.serializers import (
    ValiderVoucherSerializer,
    VoucherSerializer,
)
from apps.payments.services.paiement_service import VoucherService


# ── POST /api/payments/voucher/valider/ ─────────────────────────
@extend_schema(tags=['Vouchers'], summary='Valider un code voucher')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def valider_voucher(request):
    """
    Valider un code voucher avant de passer commande.
    Retourne la remise applicable.
    """
    serializer = ValiderVoucherSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    code             = serializer.validated_data['code']
    montant_commande = serializer.validated_data['montant_commande']

    try:
        acheteur = request.user.profil_acheteur
    except Exception:
        return Response(
            {'success': False, 'error': "Profil acheteur requis."},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        voucher, remise = VoucherService.valider_voucher(
            code=code,
            acheteur=acheteur,
            montant_commande=montant_commande,
        )
    except ValueError as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer_v = VoucherSerializer(
        voucher,
        context={'montant_commande': montant_commande}
    )

    return Response({
        'success': True,
        'data': {
            **serializer_v.data,
            'remise_appliquee': str(remise),
            'montant_apres_remise': str(montant_commande - remise),
        }
    })


# ── GET /api/payments/voucher/mes-vouchers/ ─────────────────────
@extend_schema(tags=['Vouchers'], summary='Mes vouchers')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_vouchers(request):
    """Vouchers actifs assignés à l'utilisateur connecté."""
    try:
        acheteur = request.user.profil_acheteur
    except Exception:
        return Response({'success': True, 'data': []})

    vouchers = Voucher.objects.filter(
        beneficiaire=acheteur,
        statut=Voucher.Statut.ACTIF
    ).select_related('programme')

    serializer = VoucherSerializer(vouchers, many=True)
    return Response({'success': True, 'data': serializer.data})
```

---

### `apps/payments/views/__init__.py`

```python
from .paiement_views import (
    initier_paiement,
    soumettre_preuve,
    verifier_paiement,
    mes_paiements,
)
from .voucher_views import (
    valider_voucher,
    mes_vouchers,
)

__all__ = [
    'initier_paiement', 'soumettre_preuve',
    'verifier_paiement', 'mes_paiements',
    'valider_voucher', 'mes_vouchers',
]
```

---

## ÉTAPE 4 — URLs Paiements

### `apps/payments/urls.py` ← REMPLACER le fichier vide

```python
from django.urls import path
from apps.payments import views

app_name = 'payments'

urlpatterns = [
    # Paiements
    path('initier/',          views.initier_paiement,  name='initier'),
    path('preuve/',           views.soumettre_preuve,  name='preuve'),
    path('verifier/',         views.verifier_paiement, name='verifier'),
    path('mes-paiements/',    views.mes_paiements,     name='mes_paiements'),

    # Vouchers
    path('voucher/valider/',      views.valider_voucher, name='voucher_valider'),
    path('voucher/mes-vouchers/', views.mes_vouchers,    name='mes_vouchers'),
]
```

---

## ÉTAPE 5 — Serializers Collectes

### `apps/collectes/serializers/collecte_serializers.py`

```python
from rest_framework import serializers
from apps.collectes.models import Collecte, ParticipationCollecte


class ZoneSerializer(serializers.Serializer):
    """Représentation minimale d'une zone de collecte."""
    id          = serializers.IntegerField(source='pk')
    nom         = serializers.CharField()
    departement = serializers.CharField()


class PointCollecteMinimalSerializer(serializers.Serializer):
    """Représentation minimale d'un point de collecte."""
    id      = serializers.IntegerField(source='pk')
    nom     = serializers.CharField()
    adresse = serializers.CharField()
    commune = serializers.CharField()


class CollecteMinimalSerializer(serializers.ModelSerializer):
    """Collecte vue par le producteur."""
    zone            = ZoneSerializer()
    point_collecte  = PointCollecteMinimalSerializer(allow_null=True)
    statut_label    = serializers.CharField(source='get_statut_display')
    type_label      = serializers.CharField(source='get_type_collecte_display')
    agent_nom       = serializers.SerializerMethodField()

    class Meta:
        model  = Collecte
        fields = [
            'numero_collecte', 'titre' if hasattr(Collecte, 'titre') else 'reference',
            'type_collecte', 'type_label',
            'zone', 'point_collecte',
            'date_prevue', 'heure_debut', 'heure_fin',
            'statut', 'statut_label',
            'quantite_prevue_kg',
            'instructions' if hasattr(Collecte, 'instructions') else 'notes',
            'agent_nom',
        ]

    def get_agent_nom(self, obj):
        agent_field = getattr(obj, 'agent_collecte', None) or getattr(obj, 'collecteur', None)
        if agent_field:
            return agent_field.get_full_name()
        return None


class ParticipationCollecteSerializer(serializers.ModelSerializer):
    """Participation d'un producteur à une collecte."""
    collecte        = CollecteMinimalSerializer()
    statut_label    = serializers.CharField(source='get_statut_display')

    class Meta:
        model  = ParticipationCollecte
        fields = [
            'id',
            'collecte',
            'statut',
            'statut_label',
            'quantite_prevue',
            'quantite_recue',
            'montant_paye',
            'paiement_effectue',
            'notes',
            'created_at',
        ]


class ConfirmerParticipationSerializer(serializers.Serializer):
    """Données pour confirmer une participation."""
    quantite_prevue = serializers.DecimalField(
                        max_digits=10, decimal_places=2,
                        required=False, allow_null=True,
                        help_text="Quantité en kg que le producteur prévoit d'apporter"
                      )
    notes           = serializers.CharField(
                        required=False, allow_blank=True
                      )
```

---

### `apps/collectes/serializers/__init__.py`

```python
from .collecte_serializers import (
    CollecteMinimalSerializer,
    ParticipationCollecteSerializer,
    ConfirmerParticipationSerializer,
)

__all__ = [
    'CollecteMinimalSerializer',
    'ParticipationCollecteSerializer',
    'ConfirmerParticipationSerializer',
]
```

---

## ÉTAPE 6 — Vues Collectes

### `apps/collectes/views/collecte_views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsProducteur
from apps.collectes.models import Collecte, ParticipationCollecte
from apps.collectes.serializers import (
    ParticipationCollecteSerializer,
    ConfirmerParticipationSerializer,
)


# ── GET /api/collectes/mes-participations/ ──────────────────────
@extend_schema(tags=['Collectes'], summary='Mes participations aux collectes')
@api_view(['GET'])
@permission_classes([IsProducteur])
def mes_participations(request):
    """
    Liste des collectes auxquelles le producteur est invité ou participe.
    Filtre optionnel : ?statut=invite|confirme|present|absent
    """
    producteur = request.user.profil_producteur
    statut     = request.query_params.get('statut', '')

    qs = ParticipationCollecte.objects.filter(
        producteur=producteur
    ).select_related(
        'collecte__zone',
        'collecte__point_collecte',
    ).order_by('-collecte__date_prevue')

    # Utiliser le bon nom de champ agent selon le modèle réel
    try:
        qs = qs.select_related('collecte__agent_collecte')
    except Exception:
        try:
            qs = qs.select_related('collecte__collecteur')
        except Exception:
            pass

    if statut:
        qs = qs.filter(statut=statut)

    serializer = ParticipationCollecteSerializer(qs, many=True)
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/collectes/participations/<id>/confirmer/ ─────────
@extend_schema(tags=['Collectes'], summary='Confirmer ma participation')
@api_view(['PATCH'])
@permission_classes([IsProducteur])
def confirmer_participation(request, pk):
    """
    Confirmer la participation à une collecte.
    Met à jour le statut en 'confirme' et la quantité prévue.
    """
    producteur    = request.user.profil_producteur
    participation = get_object_or_404(
        ParticipationCollecte,
        pk=pk,
        producteur=producteur
    )

    # Vérifier que la collecte est encore planifiée
    if participation.collecte.statut not in ['planifiee', 'en_cours']:
        return Response(
            {
                'success': False,
                'error': (
                    "Impossible de confirmer une participation "
                    f"pour une collecte '{participation.collecte.statut}'."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ConfirmerParticipationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    participation.statut = ParticipationCollecte.Statut.CONFIRME

    quantite_prevue = serializer.validated_data.get('quantite_prevue')
    notes           = serializer.validated_data.get('notes', '')

    # Utiliser le bon champ selon le modèle réel
    if quantite_prevue:
        if hasattr(participation, 'quantite_prevue_kg'):
            participation.quantite_prevue_kg = quantite_prevue
        elif hasattr(participation, 'quantite_prevue'):
            participation.quantite_prevue = quantite_prevue

    if notes:
        participation.notes = notes

    participation.save()

    return Response({
        'success': True,
        'data': {
            **ParticipationCollecteSerializer(participation).data,
            'message': "Participation confirmée avec succès.",
        }
    })
```

---

### `apps/collectes/views/__init__.py`

```python
from .collecte_views import mes_participations, confirmer_participation

__all__ = ['mes_participations', 'confirmer_participation']
```

---

## ÉTAPE 7 — URLs Collectes

### `apps/collectes/urls.py` ← REMPLACER le fichier vide

```python
from django.urls import path
from apps.collectes import views

app_name = 'collectes'

urlpatterns = [
    path(
        'mes-participations/',
        views.mes_participations,
        name='mes_participations'
    ),
    path(
        'participations/<int:pk>/confirmer/',
        views.confirmer_participation,
        name='confirmer_participation'
    ),
]
```

---

## ÉTAPE 8 — Vérifier `config/urls.py`

S'assurer que les routes payments et collectes sont bien enregistrées.
Si elles ne sont pas encore là, les ajouter :

```python
# config/urls.py
urlpatterns = [
    path('',              include('apps.home.urls')),
    path('admin/',        admin.site.urls),
    path('api/auth/',     include('apps.accounts.urls')),
    path('api/products/', include('apps.catalog.urls')),
    path('api/stock/',    include('apps.stock.urls')),
    path('api/orders/',   include('apps.orders.urls')),
    path('api/payments/', include('apps.payments.urls')),   # ← vérifier
    path('api/collectes/', include('apps.collectes.urls')), # ← vérifier
    path('api/geo/',      include('apps.geo.urls')),
    path('analytics/',    include('apps.analytics.urls')),
    path('api/schema/',   include('drf_spectacular.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## ÉTAPE 9 — Vérification et tests

```bash
# Vérifier
python manage.py check --settings=config.settings.development

# Lancer
python manage.py runserver --settings=config.settings.development
```

### Tests curl

```bash
BASE="http://localhost:8000"
TOKEN="<ton_access_token>"

# Initier un paiement
curl -X POST "$BASE/api/payments/initier/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "commande_numero": "CMD-2026-00001",
    "type_paiement": "cash",
    "notes": "Paiement en espèces"
  }'

# Valider un voucher
curl -X POST "$BASE/api/payments/voucher/valider/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "VCH-ABCD-1234",
    "montant_commande": "1500.00"
  }'

# Mes vouchers
curl "$BASE/api/payments/voucher/mes-vouchers/" \
  -H "Authorization: Bearer $TOKEN"

# Mes participations collectes (producteur)
curl "$BASE/api/collectes/mes-participations/" \
  -H "Authorization: Bearer $TOKEN"

# Confirmer participation
curl -X PATCH "$BASE/api/collectes/participations/1/confirmer/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quantite_prevue": "50.5", "notes": "Je serai présent"}'
```

---

## NOTE IMPORTANTE — Adaptation au modèle réel

Les serializers et vues Collectes utilisent des checks `hasattr` et
`getattr` pour s'adapter aux noms de champs réels de ton modèle
`Collecte` et `ParticipationCollecte`.

En particulier :
- `collecte.titre` OU `collecte.reference` → utiliser celui qui existe
- `collecte.instructions` OU `collecte.notes` → utiliser celui qui existe
- `collecte.agent_collecte` OU `collecte.collecteur` → utiliser celui qui existe
- `participation.quantite_prevue_kg` OU `participation.quantite_prevue`

**Vérifier les vrais noms dans tes modèles et ajuster les serializers
en conséquence avant de lancer.**

---

## RÉSUMÉ — Endpoints créés dans ce prompt

### Paiements
| Méthode | Endpoint | Auth |
|---------|----------|------|
| POST | `/api/payments/initier/` | Requis |
| POST | `/api/payments/preuve/` | Requis |
| POST | `/api/payments/verifier/` | Requis |
| GET | `/api/payments/mes-paiements/` | Requis |

### Vouchers
| Méthode | Endpoint | Auth |
|---------|----------|------|
| POST | `/api/payments/voucher/valider/` | Requis |
| GET | `/api/payments/voucher/mes-vouchers/` | Requis |

### Collectes
| Méthode | Endpoint | Auth |
|---------|----------|------|
| GET | `/api/collectes/mes-participations/` | Producteur |
| PATCH | `/api/collectes/participations/<id>/confirmer/` | Producteur |
