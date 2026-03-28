from django.urls import path
from apps.orders import views

app_name = 'orders'

urlpatterns = [
    # Panier
    path('panier/',                         views.panier_resume,  name='panier_resume'),
    path('panier/ajouter/',                 views.panier_ajouter, name='panier_ajouter'),
    path('panier/modifier/<slug:slug>/',    views.panier_modifier, name='panier_modifier'),
    path('panier/retirer/<slug:slug>/',     views.panier_retirer, name='panier_retirer'),
    path('panier/vider/',                   views.panier_vider,   name='panier_vider'),

    # Commander
    path('commander/',                      views.commander,      name='commander'),
]
