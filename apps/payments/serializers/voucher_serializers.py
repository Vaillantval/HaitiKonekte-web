from rest_framework import serializers
from apps.payments.models import Voucher, ProgrammeVoucher
from django.utils.translation import gettext_lazy as _


class ValiderVoucherSerializer(serializers.Serializer):
    """Valider un code voucher avant de passer commande."""
    code             = serializers.CharField(max_length=20)
    montant_commande = serializers.DecimalField(
                         max_digits=12, decimal_places=2
                       )


class VoucherSerializer(serializers.ModelSerializer):
    """Serializer de lecture d'un voucher."""
    programme_nom   = serializers.CharField(source='programme.nom')
    statut_label    = serializers.CharField(source='get_statut_display')
    type_label      = serializers.CharField(source='get_type_valeur_display')
    remise_calculee = serializers.SerializerMethodField()

    class Meta:
        model  = Voucher
        fields = [
            'code', 'programme_nom',
            'type_valeur', 'type_label',
            'valeur', 'montant_max',
            'montant_commande_min',
            'statut', 'statut_label',
            'date_expiration', 'est_valide',
            'remise_calculee',
        ]

    def get_remise_calculee(self, obj):
        montant = self.context.get('montant_commande')
        if montant:
            return str(obj.calculer_remise(montant))
        return None
