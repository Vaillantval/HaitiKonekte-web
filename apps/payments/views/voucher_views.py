from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.payments.models import Voucher
from apps.payments.serializers import (
    ValiderVoucherSerializer,
    VoucherSerializer,
)
from apps.payments.services.paiement_service import VoucherService


# ── POST /api/payments/voucher/valider/ ─────────────────────────
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
            status=status.HTTP_400_BAD_REQUEST,
        )

    code             = serializer.validated_data['code']
    montant_commande = serializer.validated_data['montant_commande']

    try:
        acheteur = request.user.profil_acheteur
    except Exception:
        return Response(
            {'success': False, 'error': "Profil acheteur requis."},
            status=status.HTTP_403_FORBIDDEN,
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
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer_v = VoucherSerializer(
        voucher,
        context={'montant_commande': montant_commande},
    )

    return Response({
        'success': True,
        'data': {
            **serializer_v.data,
            'remise_appliquee':    str(remise),
            'montant_apres_remise': str(montant_commande - remise),
        },
    })


# ── GET /api/payments/voucher/mes-vouchers/ ─────────────────────
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
        statut=Voucher.Statut.ACTIF,
    ).select_related('programme')

    serializer = VoucherSerializer(vouchers, many=True)
    return Response({'success': True, 'data': serializer.data})
