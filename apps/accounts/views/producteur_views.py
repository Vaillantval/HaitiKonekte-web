from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsProducteur
from apps.accounts.serializers import (
    ProducteurProfilSerializer,
    ProducteurStatsSerializer,
    CommandeProducteurSerializer,
)
from apps.orders.models import Commande
from apps.orders.services.commande_service import CommandeService
from django.utils.translation import gettext as _


# ── GET /api/auth/producteur/stats/ ────────────────────────────────────────

@extend_schema(tags=['Producteur'], summary='Statistiques dashboard producteur')
@api_view(['GET'])
@permission_classes([IsProducteur])
def producteur_stats(request):
    producteur = request.user.profil_producteur
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    commandes_qs = Commande.objects.filter(producteur=producteur)

    revenus_total = commandes_qs.filter(
        statut__in=['confirmee', 'en_preparation', 'prete', 'en_collecte', 'livree'],
        statut_paiement='paye',
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    revenus_mois = commandes_qs.filter(
        statut__in=['confirmee', 'livree'],
        statut_paiement='paye',
        created_at__gte=debut_mois,
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    alertes = 0
    try:
        from apps.stock.models import AlerteStock
        alertes = AlerteStock.objects.filter(
            produit__producteur=producteur,
            statut__in=['nouvelle', 'vue'],
        ).count()
    except Exception:
        pass

    collectes_a_venir = 0
    try:
        from apps.collectes.models import Collecte
        collectes_a_venir = Collecte.objects.filter(
            participations__producteur=producteur,
            statut='planifiee',
            date_prevue__gte=timezone.now().date(),
        ).count()
    except Exception:
        pass

    stock_faible = producteur.produits.filter(
        is_active=True,
        stock_disponible__lte=F('seuil_alerte'),
    ).count()

    stats = {
        'commandes_en_attente': commandes_qs.filter(statut='en_attente').count(),
        'commandes_confirmees': commandes_qs.filter(statut='confirmee').count(),
        'commandes_en_cours':   commandes_qs.filter(
            statut__in=['confirmee', 'en_preparation', 'prete', 'en_collecte']
        ).count(),
        'commandes_livrees':    commandes_qs.filter(statut='livree').count(),
        'commandes_total':      commandes_qs.count(),
        'revenus_total':        revenus_total,
        'revenus_mois':         revenus_mois,
        'nb_produits_actifs':   producteur.produits.filter(is_active=True).count(),
        'nb_produits_epuises':  producteur.produits.filter(statut='epuise').count(),
        'alertes_stock':        alertes,
        'stock_faible':         stock_faible,
        'collectes_a_venir':    collectes_a_venir,
        'statut':               producteur.statut,
        'statut_label':         producteur.get_statut_display(),
    }
    serializer = ProducteurStatsSerializer(stats)
    return Response({'success': True, 'data': serializer.data})


# ── GET / PATCH /api/auth/producteur/profil/ ───────────────────────────────

@extend_schema(tags=['Producteur'], summary='Profil boutique producteur')
@api_view(['GET', 'PATCH'])
@permission_classes([IsProducteur])
def producteur_profil(request):
    producteur = request.user.profil_producteur

    if request.method == 'GET':
        serializer = ProducteurProfilSerializer(
            producteur, context={'request': request}
        )
        return Response({'success': True, 'data': serializer.data})

    serializer = ProducteurProfilSerializer(
        producteur,
        data=request.data,
        partial=True,
        context={'request': request},
    )
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer.save()
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/auth/producteur/commandes/ ────────────────────────────────────

@extend_schema(operation_id='producteur_commandes_list', tags=['Producteur'], summary='Commandes reçues par le producteur')
@api_view(['GET'])
@permission_classes([IsProducteur])
def producteur_commandes(request):
    producteur = request.user.profil_producteur
    statut     = request.query_params.get('statut', '').strip()

    qs = Commande.objects.filter(
        producteur=producteur
    ).select_related(
        'acheteur__user'
    ).prefetch_related('details__produit').order_by('-created_at')

    if statut:
        qs = qs.filter(statut=statut)

    serializer = CommandeProducteurSerializer(qs, many=True)
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/auth/producteur/commandes/<numero>/ ────────────────────────────

@extend_schema(operation_id='producteur_commande_detail', tags=['Producteur'], summary='Détail commande producteur')
@api_view(['GET'])
@permission_classes([IsProducteur])
def producteur_commande_detail(request, numero):
    producteur = request.user.profil_producteur
    commande   = get_object_or_404(
        Commande,
        numero_commande=numero,
        producteur=producteur,
    )
    serializer = CommandeProducteurSerializer(commande)
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/auth/producteur/commandes/<numero>/statut/ ───────────────────

@extend_schema(tags=['Producteur'], summary='Changer statut commande')
@api_view(['PATCH'])
@permission_classes([IsProducteur])
def producteur_commande_statut(request, numero):
    producteur = request.user.profil_producteur
    commande   = get_object_or_404(
        Commande,
        numero_commande=numero,
        producteur=producteur,
    )

    action = request.data.get('action', '').strip()
    motif  = request.data.get('motif', '').strip()

    TRANSITIONS = {
        'confirmer': ([Commande.Statut.EN_ATTENTE],   Commande.Statut.CONFIRMEE),
        'preparer':  ([Commande.Statut.CONFIRMEE],    Commande.Statut.EN_PREPARATION),
        'prete':     ([Commande.Statut.EN_PREPARATION], Commande.Statut.PRETE),
        'annuler':   (
            [Commande.Statut.EN_ATTENTE, Commande.Statut.CONFIRMEE, Commande.Statut.EN_PREPARATION],
            Commande.Statut.ANNULEE,
        ),
    }

    if action not in TRANSITIONS:
        return Response(
            {'success': False, 'error': f"Action invalide. Valeurs : {list(TRANSITIONS.keys())}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    statuts_autorises, nouveau_statut = TRANSITIONS[action]
    if commande.statut not in statuts_autorises:
        return Response(
            {
                'success': False,
                'error': (
                    f"Impossible de '{action}' une commande "
                    f"avec le statut '{commande.get_statut_display()}'."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if action == 'annuler' and not motif:
        return Response(
            {'success': False, 'error': _("Le motif est requis pour annuler une commande.")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if action == 'confirmer':
            CommandeService.confirmer_commande(commande, request.user)
        elif action == 'annuler':
            CommandeService.annuler_commande(commande, request.user, motif)
        else:
            CommandeService.changer_statut(commande, nouveau_statut, effectue_par=request.user)
    except ValueError as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({
        'success': True,
        'data': {
            'numero_commande': commande.numero_commande,
            'statut':          commande.statut,
            'statut_label':    commande.get_statut_display(),
            'message':         f"Commande {action}e avec succès.",
        }
    })
