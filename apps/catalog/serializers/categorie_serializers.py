from rest_framework import serializers
from apps.catalog.models import Categorie


class CategorieSerializer(serializers.ModelSerializer):
    nb_produits = serializers.SerializerMethodField()

    class Meta:
        model  = Categorie
        fields = ['id', 'nom', 'slug', 'description',
                  'image', 'icone', 'ordre', 'nb_produits']

    def get_nb_produits(self, obj):
        return obj.nb_produits
