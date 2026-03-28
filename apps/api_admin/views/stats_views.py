from decimal import Decimal
from datetime import timedelta

from django.utils import timezone
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsSuperAdmin
from apps.accounts.models import CustomUser, Producteur, Acheteur
from apps.catalog.models import Produit
from apps.orders.models import Commande
from apps.payments.models import Paiement, Voucher
from apps.stock.models import AlerteStock
from apps.collectes.models import Collecte
from apps.api_admin.serializers.stats_serializers import GlobalStatsSerializer


# ── GET /api/admin/stats/ ────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def global_stats(request):
    """Statistiques globales de la plateforme."""
    aujourd_hui = timezone.now().date()
    debut_mois  = aujourd_hui.replace(day=1)
    il_y_a_7j   = aujourd_hui - timedelta(days=7)
    il_y_a_30j  = aujourd_hui - timedelta(days=30)

    commandes_actives = Commande.objects.filter(
        statut__in=['confirmee', 'en_preparation', 'prete', 'en_collecte', 'livree']
    )

    revenu_total = commandes_actives.filter(
        statut_paiement='paye'
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    revenu_mois = commandes_actives.filter(
        statut_paiement='paye',
        created_at__date__gte=debut_mois
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    revenu_7j = commandes_actives.filter(
        statut_paiement='paye',
        created_at__date__gte=il_y_a_7j
    ).aggregate(t=Sum('total'))['t'] or Decimal('0')

    montant_a_verifier = Paiement.objects.filter(
        statut=Paiement.Statut.SOUMIS
    ).aggregate(t=Sum('montant'))['t'] or Decimal('0')

    collectes_en_retard = Collecte.objects.filter(
        statut='planifiee',
        date_planifiee__lt=aujourd_hui
    ).count()

    stats = {
        'total_users':           CustomUser.objects.count(),
        'total_producteurs':     Producteur.objects.count(),
        'producteurs_actifs':    Producteur.objects.filter(statut='actif').count(),
        'producteurs_attente':   Producteur.objects.filter(statut='en_attente').count(),
        'total_acheteurs':       Acheteur.objects.count(),
        'nouveaux_users_30j':    CustomUser.objects.filter(
                                   created_at__date__gte=il_y_a_30j
                                 ).count(),
        'total_commandes':       Commande.objects.count(),
        'commandes_en_attente':  Commande.objects.filter(statut='en_attente').count(),
        'commandes_livrees':     Commande.objects.filter(statut='livree').count(),
        'commandes_annulees':    Commande.objects.filter(statut='annulee').count(),
        'commandes_litige':      Commande.objects.filter(statut='litige').count(),
        'commandes_mois':        Commande.objects.filter(
                                   created_at__date__gte=debut_mois
                                 ).count(),
        'revenu_total':          revenu_total,
        'revenu_mois':           revenu_mois,
        'revenu_7j':             revenu_7j,
        'paiements_a_verifier':  Paiement.objects.filter(
                                   statut=Paiement.Statut.SOUMIS
                                 ).count(),
        'montant_a_verifier':    montant_a_verifier,
        'total_produits':        Produit.objects.filter(is_active=True).count(),
        'produits_epuises':      Produit.objects.filter(statut='epuise').count(),
        'alertes_stock':         AlerteStock.objects.filter(
                                   statut__in=['nouvelle', 'vue']
                                 ).count(),
        'collectes_planifiees':  Collecte.objects.filter(statut='planifiee').count(),
        'collectes_en_cours':    Collecte.objects.filter(statut='en_cours').count(),
        'collectes_en_retard':   collectes_en_retard,
        'vouchers_actifs':       Voucher.objects.filter(statut='actif').count(),
    }

    serializer = GlobalStatsSerializer(stats)
    return Response({'success': True, 'data': serializer.data})


# ── GET /api/admin/options/ ─────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def admin_options(request):
    """
    Listes d'options pour les selects/dropdowns du dashboard admin.
    ?type=categories|producteurs|produits|zones|points|collecteurs
    """
    type_option = request.query_params.get('type', '')

    if type_option == 'categories':
        from apps.catalog.models import Categorie
        data = [
            {'id': c['id'], 'nom': c['nom'], 'slug': c['slug'], 'label': c['nom']}
            for c in Categorie.objects.filter(is_active=True).values('id', 'nom', 'slug')
        ]

    elif type_option in ('producteurs', 'producteurs_all'):
        qs = Producteur.objects.select_related('user')
        if type_option == 'producteurs':
            qs = qs.filter(statut='actif')
        data = [
            {
                'id':    p.pk,
                'nom':   p.user.get_full_name(),
                'code':  p.code_producteur,
                'label': f"{p.user.get_full_name()} ({p.code_producteur})",
            }
            for p in qs
        ]

    elif type_option == 'produits':
        data = [
            {'id': p['id'], 'nom': p['nom'], 'slug': p['slug'],
             'prix_unitaire': str(p['prix_unitaire']), 'label': p['nom']}
            for p in Produit.objects.filter(is_active=True).values('id', 'nom', 'slug', 'prix_unitaire')
        ]

    elif type_option == 'zones':
        from apps.collectes.models import ZoneCollecte
        data = [
            {'id': z['id'], 'nom': z['nom'], 'departement': z['departement'],
             'label': f"{z['nom']} ({z['departement']})"}
            for z in ZoneCollecte.objects.filter(is_active=True).values('id', 'nom', 'departement')
        ]

    elif type_option == 'points':
        from apps.collectes.models import PointCollecte
        zone_id = request.query_params.get('zone_id')
        qs = PointCollecte.objects.filter(is_active=True)
        if zone_id:
            qs = qs.filter(zone_id=zone_id)
        data = [
            {'id': p['id'], 'nom': p['nom'], 'commune': p['commune'],
             'label': f"{p['nom']} – {p['commune'] or ''}".rstrip(' –')}
            for p in qs.values('id', 'nom', 'commune')
        ]

    elif type_option == 'collecteurs':
        data = [
            {'id': u.pk, 'nom': u.get_full_name(), 'label': u.get_full_name()}
            for u in CustomUser.objects.filter(role='collecteur', is_active=True)
        ]

    else:
        return Response(
            {
                'success': False,
                'error': (
                    "Paramètre 'type' requis. "
                    "Valeurs : categories, producteurs, producteurs_all, produits, "
                    "zones, points, collecteurs"
                )
            },
            status=400
        )

    return Response({'success': True, 'data': data})
