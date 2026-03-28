from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsProducteur
from apps.catalog.models import Produit
from apps.catalog.serializers import (
    ProduitListSerializer,
    ProduitDetailSerializer,
    ProduitCreateUpdateSerializer,
)


# ── GET/POST /api/products/mes-produits/ ────────────────────────
@extend_schema(operation_id='producteur_mes_produits_list', tags=['Producteur — Catalogue'])
@api_view(['GET', 'POST'])
@permission_classes([IsProducteur])
def mes_produits(request):
    producteur = request.user.profil_producteur

    if request.method == 'GET':
        qs = Produit.objects.filter(
            producteur=producteur
        ).select_related('categorie').order_by('-created_at')

        serializer = ProduitListSerializer(
            qs, many=True, context={'request': request}
        )
        return Response({'success': True, 'data': serializer.data})

    # POST — créer un produit
    serializer = ProduitCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    statut  = 'actif' if producteur.statut == 'actif' else 'en_attente'
    produit = serializer.save(
        producteur=producteur,
        statut=statut,
        is_active=(producteur.statut == 'actif'),
    )

    return Response(
        {
            'success': True,
            'data': ProduitDetailSerializer(
                produit, context={'request': request}
            ).data,
        },
        status=status.HTTP_201_CREATED,
    )


# ── GET/PATCH/DELETE /api/products/mes-produits/<slug>/ ─────────
@extend_schema(operation_id='producteur_mon_produit_detail', tags=['Producteur — Catalogue'])
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsProducteur])
def mon_produit_detail(request, slug):
    producteur = request.user.profil_producteur
    produit    = get_object_or_404(
        Produit, slug=slug, producteur=producteur
    )

    if request.method == 'GET':
        serializer = ProduitDetailSerializer(
            produit, context={'request': request}
        )
        return Response({'success': True, 'data': serializer.data})

    if request.method == 'PATCH':
        serializer = ProduitCreateUpdateSerializer(
            produit, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response({
            'success': True,
            'data': ProduitDetailSerializer(
                produit, context={'request': request}
            ).data,
        })

    # DELETE
    produit.delete()
    return Response({
        'success': True,
        'data': {'message': 'Produit supprimé avec succès.'},
    })
