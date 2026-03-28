from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.accounts.permissions import IsSuperAdmin
from apps.accounts.models import CustomUser
from apps.accounts.serializers import RegisterSerializer, UserProfileSerializer


# ── GET /api/admin/users/ ────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def users_list(request):
    """Liste des utilisateurs avec filtres."""
    search    = request.query_params.get('search', '')
    role      = request.query_params.get('role', '')
    is_active = request.query_params.get('is_active', '')

    qs = CustomUser.objects.order_by('-created_at')

    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)  |
            Q(email__icontains=search)      |
            Q(username__icontains=search)   |
            Q(telephone__icontains=search)
        )
    if role:
        qs = qs.filter(role=role)
    if is_active:
        qs = qs.filter(is_active=(is_active.lower() == 'true'))

    data = UserProfileSerializer(
        qs, many=True, context={'request': request}
    ).data
    return Response({'success': True, 'data': data})


# ── POST /api/admin/users/create/ ───────────────────────────────
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def user_create(request):
    """Créer un utilisateur."""
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    user = serializer.save()
    return Response(
        {
            'success': True,
            'data': UserProfileSerializer(
                user, context={'request': request}
            ).data
        },
        status=status.HTTP_201_CREATED
    )


# ── GET/PATCH /api/admin/users/<id>/detail/ ─────────────────────
@api_view(['GET', 'PATCH'])
@permission_classes([IsSuperAdmin])
def user_detail(request, pk):
    """Détail ou mise à jour d'un utilisateur."""
    user = get_object_or_404(CustomUser, pk=pk)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': UserProfileSerializer(
                user, context={'request': request}
            ).data
        })

    serializer = UserProfileSerializer(
        user, data=request.data,
        partial=True,
        context={'request': request}
    )
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer.save()
    return Response({'success': True, 'data': serializer.data})


# ── PATCH /api/admin/users/<id>/toggle/ ─────────────────────────
@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
def user_toggle(request, pk):
    """Activer ou désactiver un utilisateur."""
    user           = get_object_or_404(CustomUser, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return Response({
        'success': True,
        'data': {
            'id':        user.pk,
            'is_active': user.is_active,
            'message':   f"Compte {'activé' if user.is_active else 'désactivé'}."
        }
    })
