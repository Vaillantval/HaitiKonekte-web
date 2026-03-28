from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema

from apps.accounts.models import CustomUser
from apps.accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    FCMTokenSerializer,
)


def _get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
    }


def _user_data(user, request=None):
    return UserProfileSerializer(user, context={'request': request}).data


# ── POST /api/auth/register/ ────────────────────────────────────────────────

@extend_schema(tags=['Auth'], summary='Inscription')
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user   = serializer.save()
    tokens = _get_tokens(user)
    return Response(
        {'success': True, 'data': {**tokens, 'user': _user_data(user, request)}},
        status=status.HTTP_201_CREATED,
    )


# ── POST /api/auth/login/ ───────────────────────────────────────────────────

@extend_schema(tags=['Auth'], summary='Connexion')
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user   = serializer.validated_data['user']
    tokens = _get_tokens(user)
    return Response(
        {'success': True, 'data': {**tokens, 'user': _user_data(user, request)}},
    )


# ── POST /api/auth/logout/ ──────────────────────────────────────────────────

@extend_schema(tags=['Auth'], summary='Déconnexion')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get('refresh', '').strip()
    fcm_token     = request.data.get('fcm_token', '').strip()

    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass

    # Désabonner le device FCM
    token_to_remove = fcm_token or request.user.fcm_token
    if token_to_remove:
        try:
            from apps.emails.fcm_service import unsubscribe_from_all_topics
            unsubscribe_from_all_topics(token_to_remove)
        except Exception:
            pass
        request.user.fcm_token = ''
        request.user.save(update_fields=['fcm_token'])

    return Response({'success': True, 'data': {'message': 'Déconnexion réussie.'}})


# ── GET / PATCH /api/auth/me/ ──────────────────────────────────────────────

@extend_schema(tags=['Auth'], summary='Profil utilisateur connecté')
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == 'GET':
        return Response({'success': True, 'data': _user_data(request.user, request)})

    serializer = UserProfileSerializer(
        request.user,
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
    return Response({'success': True, 'data': _user_data(request.user, request)})


# ── POST /api/auth/change-password/ ────────────────────────────────────────

@extend_schema(tags=['Auth'], summary='Changer le mot de passe')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(
        data=request.data, context={'request': request}
    )
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save()
    return Response({'success': True, 'data': {'message': 'Mot de passe modifié avec succès.'}})


# ── POST /api/auth/fcm-token/ ───────────────────────────────────────────────

@extend_schema(tags=['Auth'], summary='Enregistrer token FCM')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fcm_token(request):
    serializer = FCMTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    token = serializer.validated_data['fcm_token']
    request.user.fcm_token = token
    request.user.save(update_fields=['fcm_token'])

    # Abonner au topic du rôle
    topic = f"role_{request.user.role}"
    try:
        from apps.emails.fcm_service import subscribe_to_topic
        subscribe_to_topic(token, topic)
    except Exception:
        pass

    return Response({
        'success': True,
        'data': {
            'message':          'Token enregistré.',
            'role':             request.user.role,
            'topic_subscribed': topic,
        }
    })


# ── GET /api/auth/commandes/ ────────────────────────────────────────────────

@extend_schema(operation_id='auth_commandes_list', tags=['Acheteur'], summary='Mes commandes')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def acheteur_commandes(request):
    from apps.orders.models import Commande
    from apps.accounts.serializers import CommandeProducteurSerializer
    try:
        acheteur = request.user.profil_acheteur
    except Exception:
        return Response(
            {'success': False, 'error': 'Profil acheteur introuvable.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    commandes = Commande.objects.filter(
        acheteur=acheteur
    ).select_related('producteur__user', 'acheteur__user').prefetch_related(
        'details__produit'
    ).order_by('-created_at')

    serializer = CommandeProducteurSerializer(commandes, many=True)
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/auth/commandes/<numero>/ ──────────────────────────────────────

@extend_schema(operation_id='auth_commande_detail', tags=['Acheteur'], summary='Détail commande acheteur')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def acheteur_commande_detail(request, numero):
    from django.shortcuts import get_object_or_404
    from apps.orders.models import Commande
    from apps.accounts.serializers import CommandeProducteurSerializer
    try:
        acheteur = request.user.profil_acheteur
    except Exception:
        return Response(
            {'success': False, 'error': 'Profil acheteur introuvable.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    commande   = get_object_or_404(Commande, numero_commande=numero, acheteur=acheteur)
    serializer = CommandeProducteurSerializer(commande)
    return Response({'success': True, 'data': serializer.data})
