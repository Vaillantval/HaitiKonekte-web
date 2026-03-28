from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.catalog.models import Produit, Categorie
from apps.catalog.serializers import (
    ProduitListSerializer,
    ProduitDetailSerializer,
    CategorieSerializer,
)
from apps.catalog.filters import ProduitFilter


class ProduitPagination(PageNumberPagination):
    page_size             = 20
    page_size_query_param = 'page_size'
    max_page_size         = 100


# ── GET /api/products/ ──────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def produits_list(request):
    """
    Liste paginée des produits actifs avec filtres.
    Filtres : search, categorie, departement, producteur_id,
              prix_min, prix_max, featured, page, page_size
    """
    qs = Produit.objects.filter(
        is_active=True,
        stock_disponible__gt=0,
    ).select_related(
        'categorie',
        'producteur__user',
    ).order_by('-is_featured', '-created_at')

    filterset = ProduitFilter(request.query_params, queryset=qs)
    if not filterset.is_valid():
        return Response(
            {'success': False, 'error': filterset.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    qs = filterset.qs

    paginator  = ProduitPagination()
    page       = paginator.paginate_queryset(qs, request)
    serializer = ProduitListSerializer(
        page, many=True, context={'request': request}
    )

    return Response({
        'success': True,
        'data': {
            'count':    paginator.page.paginator.count,
            'next':     paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results':  serializer.data,
        },
    })


# ── GET /api/products/public/<slug>/ ────────────────────────────
@extend_schema(operation_id='products_produit_detail', responses=ProduitDetailSerializer, tags=['Catalogue public'])
@api_view(['GET'])
@permission_classes([AllowAny])
def produit_detail(request, slug):
    """Détail complet d'un produit avec galerie et similaires."""
    produit    = get_object_or_404(Produit, slug=slug, is_active=True)
    serializer = ProduitDetailSerializer(
        produit, context={'request': request}
    )
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/products/categories/ ──────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def categories_list(request):
    """Toutes les catégories actives."""
    categories = Categorie.objects.filter(
        is_active=True
    ).order_by('ordre', 'nom')
    serializer = CategorieSerializer(categories, many=True)
    return Response({'success': True, 'data': serializer.data})
