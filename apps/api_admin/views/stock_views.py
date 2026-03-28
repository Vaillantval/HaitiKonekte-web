from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.stock.models import Lot, MouvementStock, AlerteStock
from apps.stock.services.stock_service import StockService


def _lot_data(lot):
    return {
        'id':                lot.pk,
        'numero_lot':        lot.numero_lot,
        'produit':           lot.produit.nom,
        'producteur':        lot.produit.producteur.user.get_full_name(),
        'quantite_initiale': lot.quantite_initiale,
        'quantite_actuelle': lot.quantite_actuelle,
        'quantite_vendue':   lot.quantite_vendue,
        'taux_ecoulement':   lot.taux_ecoulement,
        'statut':            lot.statut,
        'date_recolte':      str(lot.date_recolte) if lot.date_recolte else None,
        'lieu_stockage':     lot.lieu_stockage,
        'created_at':        lot.created_at.isoformat(),
    }


# ── GET /api/admin/stocks/lots/ ──────────────────────────────────
@extend_schema(operation_id='admin_lots_list', tags=['Admin — Stocks'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def lots_list(request):
    """Liste des lots avec filtres."""
    search        = request.query_params.get('search', '')
    statut        = request.query_params.get('statut', '')
    producteur_id = request.query_params.get('producteur_id', '')

    qs = Lot.objects.select_related(
        'produit__producteur__user'
    ).order_by('-created_at')

    if search:
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
@extend_schema(operation_id='admin_lot_detail', tags=['Admin — Stocks'])
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
            'id':           a.pk,
            'produit':      a.produit.nom,
            'producteur':   a.produit.producteur.user.get_full_name(),
            'niveau':       a.niveau,
            'stock_actuel': a.stock_actuel,
            'seuil':        a.seuil,
            'message':      a.message,
            'statut':       a.statut,
            'created_at':   a.created_at.isoformat(),
        }
        for a in qs
    ]
    return Response({'success': True, 'data': data})


# ── GET /api/admin/stocks/mouvements/ ───────────────────────────
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def mouvements_stock(request):
    """Historique des mouvements de stock."""
    qs = MouvementStock.objects.select_related(
        'produit', 'effectue_par'
    ).order_by('-created_at')[:100]

    data = [
        {
            'id':             m.pk,
            'produit':        m.produit.nom,
            'type_mouvement': m.get_type_mouvement_display(),
            'quantite':       m.quantite,
            'stock_avant':    m.stock_avant,
            'stock_apres':    m.stock_apres,
            'motif':          m.motif,
            'effectue_par':   m.effectue_par.get_full_name() if m.effectue_par else None,
            'created_at':     m.created_at.isoformat(),
        }
        for m in qs
    ]
    return Response({'success': True, 'data': data})
