from rest_framework import serializers
from apps.payments.models import Paiement
from apps.orders.models import Commande
from django.utils.translation import gettext_lazy as _


class InitierPaiementSerializer(serializers.Serializer):
    """Données pour initier un paiement."""
    commande_numero   = serializers.CharField()
    type_paiement     = serializers.ChoiceField(
                          choices=['moncash', 'natcash', 'virement', 'cash']
                        )
    numero_expediteur = serializers.CharField(
                          required=False, allow_blank=True,
                          help_text="Numéro MonCash/NatCash expéditeur"
                        )
    notes             = serializers.CharField(
                          required=False, allow_blank=True
                        )

    def validate_commande_numero(self, value):
        try:
            return Commande.objects.get(numero_commande=value)
        except Commande.DoesNotExist:
            raise serializers.ValidationError(
                f"Commande '{value}' introuvable."
            )


class SoumettrePreuveSerializer(serializers.Serializer):
    """Données pour soumettre une preuve de paiement."""
    paiement_id    = serializers.IntegerField()
    preuve_image   = serializers.ImageField()
    id_transaction = serializers.CharField(
                       required=False, allow_blank=True
                     )
    montant_recu   = serializers.DecimalField(
                       max_digits=12, decimal_places=2,
                       required=False, allow_null=True
                     )


class VerifierPaiementSerializer(serializers.Serializer):
    """Vérifier le statut d'un paiement."""
    paiement_id    = serializers.IntegerField(required=False)
    id_transaction = serializers.CharField(
                       required=False, allow_blank=True
                     )

    def validate(self, data):
        if not data.get('paiement_id') and not data.get('id_transaction'):
            raise serializers.ValidationError(
                _("Fournir 'paiement_id' ou 'id_transaction'.")
            )
        return data


class PaiementSerializer(serializers.ModelSerializer):
    """Serializer de lecture d'un paiement."""
    type_label      = serializers.CharField(
                        source='get_type_paiement_display'
                      )
    statut_label    = serializers.CharField(
                        source='get_statut_display'
                      )
    commande_numero = serializers.CharField(
                        source='commande.numero_commande'
                      )
    acheteur        = serializers.CharField(
                        source='commande.acheteur.user.get_full_name'
                      )

    class Meta:
        model  = Paiement
        fields = [
            'id', 'reference', 'commande_numero', 'acheteur',
            'type_paiement', 'type_label',
            'statut', 'statut_label',
            'montant', 'montant_recu',
            'numero_expediteur', 'id_transaction',
            'preuve_image', 'notes',
            'date_verification', 'created_at',
        ]
