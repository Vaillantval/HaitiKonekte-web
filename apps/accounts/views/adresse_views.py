from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.models import Adresse
from apps.accounts.serializers import AdresseSerializer


# ── GET / POST /api/auth/adresses/ ─────────────────────────────────────────

@extend_schema(operation_id='auth_adresses_list', tags=['Adresses'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def adresses_list(request):
    if request.method == 'GET':
        adresses   = Adresse.objects.filter(user=request.user)
        serializer = AdresseSerializer(adresses, many=True)
        return Response({'success': True, 'data': serializer.data})

    serializer = AdresseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    adresse = serializer.save(user=request.user)
    return Response(
        {'success': True, 'data': AdresseSerializer(adresse).data},
        status=status.HTTP_201_CREATED,
    )


# ── GET / PUT / PATCH / DELETE /api/auth/adresses/<pk>/ ────────────────────

@extend_schema(operation_id='auth_adresse_detail', tags=['Adresses'])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def adresse_detail(request, pk):
    adresse = get_object_or_404(Adresse, pk=pk, user=request.user)

    if request.method == 'GET':
        return Response({'success': True, 'data': AdresseSerializer(adresse).data})

    if request.method in ['PUT', 'PATCH']:
        serializer = AdresseSerializer(
            adresse,
            data=request.data,
            partial=(request.method == 'PATCH'),
        )
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response({'success': True, 'data': serializer.data})

    adresse.delete()
    return Response(
        {'success': True, 'data': {'message': 'Adresse supprimée.'}},
        status=status.HTTP_200_OK,
    )


# ── PATCH /api/auth/adresses/<pk>/default/ ─────────────────────────────────

@extend_schema(tags=['Adresses'])
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def adresse_set_default(request, pk):
    adresse            = get_object_or_404(Adresse, pk=pk, user=request.user)
    adresse.is_default = True
    adresse.save()
    return Response({
        'success': True,
        'data': {
            'message': 'Adresse définie comme adresse par défaut.',
            'adresse': AdresseSerializer(adresse).data,
        }
    })
