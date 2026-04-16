from rest_framework import serializers
from apps.catalog.models import Categorie
from django.utils.translation import gettext_lazy as _


class CategorieSerializer(serializers.ModelSerializer):
    nb_produits = serializers.SerializerMethodField()
    parent_nom  = serializers.SerializerMethodField()
    parent_id   = serializers.PrimaryKeyRelatedField(
        source='parent',
        queryset=Categorie.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model  = Categorie
        fields = [
            'id', 'nom', 'slug', 'description',
            'image', 'icone', 'ordre', 'is_active',
            'parent_id', 'parent_nom', 'nb_produits',
        ]
        read_only_fields = ['slug']

    def get_nb_produits(self, obj):
        return obj.nb_produits

    def get_parent_nom(self, obj):
        return obj.parent.nom if obj.parent else None
