from django.urls import path
from apps.catalog import views

app_name = 'catalog'

urlpatterns = [
    # Catalogue public
    path('',                            views.produits_list,   name='produits_list'),
    path('categories/',                 views.categories_list, name='categories_list'),
    path('public/<slug:slug>/',         views.produit_detail,  name='produit_detail'),

    # Mes produits (producteur connecté)
    path('mes-produits/',               views.mes_produits,        name='mes_produits'),
    path('mes-produits/<slug:slug>/',   views.mon_produit_detail,  name='mon_produit_detail'),
]
