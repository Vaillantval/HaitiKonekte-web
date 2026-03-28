from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsSuperAdmin
from apps.accounts.models import Acheteur
from apps.payments.models import Voucher, ProgrammeVoucher
from apps.payments.serializers import VoucherSerializer


@extend_schema(operation_id='admin_acheteurs_list', tags=['Admin — Acheteurs'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def acheteurs_list(request):
    qs   = Acheteur.objects.select_related('user').order_by('-created_at')
    data = [
        {
            'id':               a.pk,
            'full_name':        a.user.get_full_name(),
            'email':            a.user.email,
            'telephone':        a.user.telephone,
            'type_acheteur':    a.type_acheteur,
            'type_label':       a.get_type_acheteur_display(),
            'nom_organisation': a.nom_organisation,
            'departement':      a.departement,
            'is_active':        a.user.is_active,
            'total_commandes':  a.total_commandes,
            'total_depense':    str(a.total_depense),
            'created_at':       a.created_at.isoformat(),
        }
        for a in qs
    ]
    return Response({'success': True, 'data': data})


@extend_schema(operation_id='admin_acheteur_detail', tags=['Admin — Acheteurs'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def acheteur_detail(request, pk):
    a = get_object_or_404(Acheteur, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id':               a.pk,
            'full_name':        a.user.get_full_name(),
            'email':            a.user.email,
            'telephone':        a.user.telephone,
            'type_acheteur':    a.type_acheteur,
            'type_label':       a.get_type_acheteur_display(),
            'nom_organisation': a.nom_organisation,
            'adresse':          a.adresse,
            'ville':            a.ville,
            'departement':      a.departement,
            'is_active':        a.user.is_active,
            'total_commandes':  a.total_commandes,
            'total_depense':    str(a.total_depense),
        }
    })


@extend_schema(operation_id='admin_vouchers_list', tags=['Admin — Vouchers'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def vouchers_list(request):
    qs = Voucher.objects.select_related('programme', 'beneficiaire__user')
    return Response({
        'success': True,
        'data': VoucherSerializer(qs, many=True).data
    })


@extend_schema(operation_id='admin_voucher_detail', tags=['Admin — Vouchers'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def voucher_detail(request, pk):
    v = get_object_or_404(Voucher, pk=pk)
    return Response({'success': True, 'data': VoucherSerializer(v).data})


@extend_schema(operation_id='admin_programmes_list', tags=['Admin — Vouchers'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def programmes_list(request):
    progs = ProgrammeVoucher.objects.all()
    data  = [
        {
            'id':             p.pk,
            'nom':            p.nom,
            'code_programme': p.code_programme,
            'type_programme': p.get_type_programme_display(),
            'budget_total':   str(p.budget_total) if p.budget_total else None,
            'budget_utilise': str(p.budget_utilise),
            'est_en_cours':   p.est_en_cours,
            'is_active':      p.is_active,
        }
        for p in progs
    ]
    return Response({'success': True, 'data': data})


@extend_schema(operation_id='admin_programme_detail', tags=['Admin — Vouchers'])
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def programme_detail(request, pk):
    p = get_object_or_404(ProgrammeVoucher, pk=pk)
    return Response({
        'success': True,
        'data': {
            'id':             p.pk,
            'nom':            p.nom,
            'code_programme': p.code_programme,
            'description':    p.description,
            'budget_total':   str(p.budget_total) if p.budget_total else None,
            'budget_utilise': str(p.budget_utilise),
            'budget_restant': str(p.budget_restant) if p.budget_restant else None,
            'nb_vouchers':    p.vouchers.count(),
        }
    })


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def adresses_list_admin(request):
    from apps.accounts.models import Adresse
    from apps.accounts.serializers import AdresseSerializer
    qs = Adresse.objects.select_related('user').order_by('-created_at')
    return Response({
        'success': True,
        'data': AdresseSerializer(qs, many=True).data
    })
