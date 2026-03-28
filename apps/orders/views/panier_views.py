from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.orders.models import Panier, LignePanier
from apps.orders.serializers import PanierSerializer
from apps.catalog.models import Produit


def _get_or_create_panier(user):
    """Récupère ou crée le panier de l'utilisateur."""
    panier, _ = Panier.objects.get_or_create(user=user)
    return panier


def _panier_response(panier, request):
    """Retourne la réponse standardisée du panier."""
    serializer = PanierSerializer(panier, context={'request': request})
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/orders/panier/ ──────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def panier_resume(request):
    """Résumé du panier de l'utilisateur connecté."""
    panier = _get_or_create_panier(request.user)
    return _panier_response(panier, request)


# ── POST /api/orders/panier/ajouter/ ───────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def panier_ajouter(request):
    """
    Ajouter un produit au panier.
    Body : { "slug": "banane-ti-malice", "quantite": 2 }
    """
    slug     = request.data.get('slug')
    quantite = int(request.data.get('quantite', 1))

    if not slug:
        return Response(
            {'success': False, 'error': "Le champ 'slug' est requis."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if quantite <= 0:
        return Response(
            {'success': False, 'error': "La quantité doit être supérieure à 0."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    produit = get_object_or_404(Produit, slug=slug, is_active=True)

    if produit.stock_reel < quantite:
        return Response(
            {
                'success': False,
                'error': (
                    f"Stock insuffisant pour '{produit.nom}'. "
                    f"Disponible : {produit.stock_reel} "
                    f"{produit.get_unite_vente_display()}."
                ),
            },
            status=status.HTTP_409_CONFLICT,
        )

    panier = _get_or_create_panier(request.user)

    ligne, created = LignePanier.objects.get_or_create(
        panier=panier,
        produit=produit,
        defaults={'quantite': quantite},
    )

    if not created:
        new_qty = ligne.quantite + quantite
        if produit.stock_reel < new_qty:
            return Response(
                {
                    'success': False,
                    'error': (
                        f"Stock insuffisant. "
                        f"Vous avez déjà {ligne.quantite} "
                        f"{produit.get_unite_vente_display()} dans votre panier."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )
        ligne.quantite = new_qty
        ligne.save()

    return _panier_response(panier, request)


# ── PATCH /api/orders/panier/modifier/<slug>/ ───────────────────
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def panier_modifier(request, slug):
    """
    Modifier la quantité d'un article dans le panier.
    Body : { "quantite": 3 }
    """
    quantite = int(request.data.get('quantite', 0))

    if quantite <= 0:
        return Response(
            {'success': False, 'error': "La quantité doit être supérieure à 0."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    produit = get_object_or_404(Produit, slug=slug, is_active=True)
    panier  = get_object_or_404(Panier, user=request.user)
    ligne   = get_object_or_404(LignePanier, panier=panier, produit=produit)

    if produit.stock_reel < quantite:
        return Response(
            {
                'success': False,
                'error': (
                    f"Stock insuffisant. "
                    f"Disponible : {produit.stock_reel} "
                    f"{produit.get_unite_vente_display()}."
                ),
            },
            status=status.HTTP_409_CONFLICT,
        )

    ligne.quantite = quantite
    ligne.save()

    return _panier_response(panier, request)


# ── DELETE /api/orders/panier/retirer/<slug>/ ───────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def panier_retirer(request, slug):
    """Retirer un produit du panier."""
    produit = get_object_or_404(Produit, slug=slug)
    panier  = get_object_or_404(Panier, user=request.user)
    ligne   = get_object_or_404(LignePanier, panier=panier, produit=produit)

    ligne.delete()
    return _panier_response(panier, request)


# ── DELETE /api/orders/panier/vider/ ───────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def panier_vider(request):
    """Vider entièrement le panier."""
    panier = get_object_or_404(Panier, user=request.user)
    panier.items.all().delete()
    return _panier_response(panier, request)
