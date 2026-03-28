from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.collectes.models import (
    Collecte, ParticipationCollecte,
    ZoneCollecte, PointCollecte,
)
from apps.collectes.services.collecte_service import CollecteService
from apps.accounts.models import Producteur


def _collecte_data(c):
    """Sérialisation basique d'une collecte."""
    return {
        'id':             c.pk,
        'reference':      c.reference,
        'statut':         c.statut,
        'zone':           c.zone.nom if c.zone else None,
        'point_collecte': c.point_collecte.nom if c.point_collecte else None,
        'date_planifiee': str(c.date_planifiee),
        'collecteur':     c.collecteur.get_full_name() if c.collecteur else None,
        'nb_producteurs': c.participations.count(),
        'notes':          c.notes,
        'created_at':     c.created_at.isoformat(),
    }


# ── GET /api/admin/collectes/ ────────────────────────────────────
@extend_schema(operation_id='admin_collectes_list', tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def collectes_list(request):
    """Toutes les collectes avec filtre par statut."""
    statut = request.query_params.get('statut', '')

    qs = Collecte.objects.select_related(
        'zone', 'point_collecte', 'collecteur'
    ).prefetch_related('participations').order_by('-created_at')

    if statut:
        qs = qs.filter(statut=statut)

    return Response({
        'success': True,
        'data': [_collecte_data(c) for c in qs]
    })


# ── POST /api/admin/collectes/create/ ───────────────────────────
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

    collecteur = None
    agent_id   = request.data.get('agent_id')
    if agent_id:
        from apps.accounts.models import CustomUser
        collecteur = get_object_or_404(CustomUser, pk=agent_id)

    try:
        collecte = CollecteService.planifier_collecte(
            zone=zone,
            point_collecte=point_collecte,
            date_planifiee=request.data.get('date_planifiee') or request.data.get('date_prevue'),
            collecteur=collecteur,
            heure_debut=request.data.get('heure_debut'),
            heure_fin=request.data.get('heure_fin'),
            notes=request.data.get('notes', '') or request.data.get('instructions', ''),
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Inscrire les producteurs si fournis
    for item in request.data.get('producteurs', []):
        p = Producteur.objects.filter(pk=item.get('producteur_id')).first()
        if p:
            CollecteService.inscrire_producteur(
                collecte=collecte,
                producteur=p,
                quantite_prevue=item.get('quantite_prevue', 0),
            )

    return Response(
        {'success': True, 'data': _collecte_data(collecte)},
        status=status.HTTP_201_CREATED
    )


# ── GET /api/admin/collectes/<id>/ ──────────────────────────────
@extend_schema(operation_id='admin_collecte_detail', tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def collecte_detail(request, pk):
    collecte = get_object_or_404(Collecte, pk=pk)
    return Response({'success': True, 'data': _collecte_data(collecte)})


# ── PATCH /api/admin/collectes/<id>/statut/ ─────────────────────
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
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def collecte_add_participation(request, pk):
    """Ajouter un producteur à une collecte."""
    collecte      = get_object_or_404(Collecte, pk=pk)
    producteur_id = request.data.get('producteur_id')
    producteur    = get_object_or_404(Producteur, pk=producteur_id)

    part, created = ParticipationCollecte.objects.get_or_create(
        collecte=collecte,
        producteur=producteur,
        defaults={
            'statut': ParticipationCollecte.Statut.INSCRIT,
        }
    )

    return Response(
        {
            'success': True,
            'data': {
                'id':         part.pk,
                'producteur': producteur.user.get_full_name(),
                'statut':     part.statut,
                'created':    created,
            }
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )


# ── PATCH /api/admin/collectes/participations/<id>/statut/ ──────
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def participation_statut(request, pk):
    """Changer le statut d'une participation."""
    part   = get_object_or_404(ParticipationCollecte, pk=pk)
    statut = request.data.get('statut')

    STATUTS = ['inscrit', 'confirme', 'present', 'absent', 'annule']
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


# ── GET /api/admin/zones/ ────────────────────────────────────────
@extend_schema(operation_id='admin_zones_list', tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def zones_list(request):
    zones = ZoneCollecte.objects.filter(is_active=True)
    data  = [
        {'id': z.pk, 'nom': z.nom, 'departement': z.departement}
        for z in zones
    ]
    return Response({'success': True, 'data': data})


@extend_schema(operation_id='admin_zone_detail', tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def zone_detail(request, pk):
    z = get_object_or_404(ZoneCollecte, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id':          z.pk,
            'nom':         z.nom,
            'departement': z.departement,
            'description': z.description,
        }
    })


# ── GET /api/admin/points/ ───────────────────────────────────────
@extend_schema(operation_id='admin_points_list', tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def points_list(request):
    points = PointCollecte.objects.filter(is_active=True)
    data   = [
        {
            'id':      p.pk,
            'nom':     p.nom,
            'commune': p.commune,
            'adresse': p.adresse,
        }
        for p in points
    ]
    return Response({'success': True, 'data': data})


@extend_schema(operation_id='admin_point_detail', tags=['Admin — Collectes'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def point_detail(request, pk):
    p = get_object_or_404(PointCollecte, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id':          p.pk,
            'nom':         p.nom,
            'commune':     p.commune,
            'adresse':     p.adresse,
            'responsable': p.responsable,
            'telephone':   p.telephone,
            'is_active':   p.is_active,
        }
    })
