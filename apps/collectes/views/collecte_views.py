from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import IsProducteur
from apps.collectes.models import Collecte, ParticipationCollecte
from apps.collectes.serializers import (
    ParticipationCollecteSerializer,
    ConfirmerParticipationSerializer,
)
from django.utils.translation import gettext as _


# ── GET /api/collectes/mes-participations/ ──────────────────────
@api_view(['GET'])
@permission_classes([IsProducteur])
def mes_participations(request):
    """
    Liste des collectes auxquelles le producteur est invité ou participe.
    Filtre optionnel : ?statut=inscrit|confirme|present|absent
    """
    producteur = request.user.profil_producteur
    statut     = request.query_params.get('statut', '')

    qs = ParticipationCollecte.objects.filter(
        producteur=producteur
    ).select_related(
        'collecte__zone',
        'collecte__point_collecte',
        'collecte__collecteur',
    ).order_by('-collecte__date_planifiee')

    if statut:
        qs = qs.filter(statut=statut)

    serializer = ParticipationCollecteSerializer(qs, many=True)
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/collectes/participations/<id>/confirmer/ ─────────
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
        producteur=producteur,
    )

    if participation.collecte.statut not in ['planifiee', 'en_cours']:
        return Response(
            {
                'success': False,
                'error': (
                    "Impossible de confirmer une participation "
                    f"pour une collecte '{participation.collecte.get_statut_display()}'."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ConfirmerParticipationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    participation.statut = ParticipationCollecte.Statut.CONFIRME

    quantite_prevue = serializer.validated_data.get('quantite_prevue')
    notes           = serializer.validated_data.get('notes', '')

    if quantite_prevue is not None:
        participation.quantite_prevue = int(quantite_prevue)

    if notes:
        participation.notes = notes

    participation.save()

    return Response({
        'success': True,
        'data': {
            **ParticipationCollecteSerializer(participation).data,
            'message': _("Participation confirmée avec succès."),
        },
    })
