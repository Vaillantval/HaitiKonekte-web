from rest_framework import serializers
from apps.accounts.models import Adresse


class AdresseSerializer(serializers.ModelSerializer):
    departement_display  = serializers.CharField(source='get_departement_display',  read_only=True)
    type_adresse_display = serializers.CharField(source='get_type_adresse_display', read_only=True)
    user_id              = serializers.IntegerField(source='user.pk',              read_only=True)
    user_nom             = serializers.SerializerMethodField()

    class Meta:
        model  = Adresse
        fields = [
            'id', 'user_id', 'user_nom',
            'libelle', 'nom_complet', 'telephone',
            'rue', 'commune', 'departement', 'departement_display',
            'section_communale', 'details',
            'type_adresse', 'type_adresse_display',
            'is_default', 'created_at',
        ]
        read_only_fields = [
            'id', 'created_at',
            'departement_display', 'type_adresse_display',
            'user_id', 'user_nom',
        ]

    def get_user_nom(self, obj):
        return obj.user.get_full_name() or obj.user.username
