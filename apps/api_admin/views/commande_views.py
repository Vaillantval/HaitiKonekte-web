from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.orders.models import Commande
from apps.orders.services.commande_service import CommandeService
from apps.accounts.serializers.producteur_serializers import CommandeProducteurSerializer


# ── GET /api/admin/commandes/ ────────────────────────────────────
@extend_schema(operation_id='admin_commandes_list', tags=['Admin — Commandes'])
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
        qs = qs.filter(
            Q(numero_commande__icontains=search)             |
            Q(acheteur__user__first_name__icontains=search)  |
            Q(acheteur__user__last_name__icontains=search)   |
            Q(producteur__user__first_name__icontains=search)
        )

    serializer = CommandeProducteurSerializer(qs, many=True)
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/admin/commandes/<numero>/ ──────────────────────────
@extend_schema(operation_id='admin_commande_detail', tags=['Admin — Commandes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def commande_detail(request, numero):
    """Détail complet d'une commande."""
    commande   = get_object_or_404(Commande, numero_commande=numero)
    serializer = CommandeProducteurSerializer(commande)
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/admin/commandes/<numero>/statut/ ─────────────────
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
