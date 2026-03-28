import django_filters
from apps.catalog.models import Produit


class ProduitFilter(django_filters.FilterSet):
    search        = django_filters.CharFilter(method='filter_search')
    categorie     = django_filters.CharFilter(field_name='categorie__slug')
    departement   = django_filters.CharFilter(
                      field_name='producteur__departement'
                    )
    producteur_id = django_filters.NumberFilter(
                      field_name='producteur__id'
                    )
    prix_min      = django_filters.NumberFilter(
                      field_name='prix_unitaire', lookup_expr='gte'
                    )
    prix_max      = django_filters.NumberFilter(
                      field_name='prix_unitaire', lookup_expr='lte'
                    )
    featured      = django_filters.BooleanFilter(field_name='is_featured')

    class Meta:
        model  = Produit
        fields = [
            'categorie', 'departement', 'producteur_id',
            'prix_min', 'prix_max', 'featured',
        ]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(nom__icontains=value)                     |
            Q(variete__icontains=value)                 |
            Q(description__icontains=value)             |
            Q(origine__icontains=value)                 |
            Q(categorie__nom__icontains=value)          |
            Q(producteur__commune__icontains=value)
        )
