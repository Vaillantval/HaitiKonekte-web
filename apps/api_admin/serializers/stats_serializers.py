from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class GlobalStatsSerializer(serializers.Serializer):
    """Statistiques globales pour le dashboard admin."""
    # Utilisateurs
    total_users           = serializers.IntegerField()
    total_producteurs     = serializers.IntegerField()
    producteurs_actifs    = serializers.IntegerField()
    producteurs_attente   = serializers.IntegerField()
    total_acheteurs       = serializers.IntegerField()
    nouveaux_users_30j    = serializers.IntegerField()

    # Commandes
    total_commandes       = serializers.IntegerField()
    commandes_en_attente  = serializers.IntegerField()
    commandes_livrees     = serializers.IntegerField()
    commandes_annulees    = serializers.IntegerField()
    commandes_litige      = serializers.IntegerField()
    commandes_mois        = serializers.IntegerField()

    # Revenus
    revenu_total          = serializers.DecimalField(max_digits=14, decimal_places=2)
    revenu_mois           = serializers.DecimalField(max_digits=14, decimal_places=2)
    revenu_7j             = serializers.DecimalField(max_digits=14, decimal_places=2)

    # Paiements
    paiements_a_verifier  = serializers.IntegerField()
    montant_a_verifier    = serializers.DecimalField(max_digits=14, decimal_places=2)

    # Produits & Stock
    total_produits        = serializers.IntegerField()
    produits_epuises      = serializers.IntegerField()
    alertes_stock         = serializers.IntegerField()

    # Collectes
    collectes_planifiees  = serializers.IntegerField()
    collectes_en_cours    = serializers.IntegerField()
    collectes_en_retard   = serializers.IntegerField()

    # Vouchers
    vouchers_actifs       = serializers.IntegerField()
