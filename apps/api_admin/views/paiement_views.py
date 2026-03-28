from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import IsSuperAdmin
from apps.payments.models import Paiement
from apps.payments.serializers import PaiementSerializer
from apps.payments.services.paiement_service import PaiementService


# ── GET /api/admin/paiements/ ────────────────────────────────────
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
