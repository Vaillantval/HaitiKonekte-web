from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [

    # ── Auth ─────────────────────────────────────────────────────────────────
    path('register/',        views.register,        name='register'),
    path('login/',           views.login,           name='login'),
    path('logout/',          views.logout,          name='logout'),
    path('token/refresh/',   TokenRefreshView.as_view(), name='token_refresh'),
    path('me/',              views.me,              name='me'),
    path('change-password/', views.change_password, name='change_password'),
    path('fcm-token/',       views.fcm_token,       name='fcm_token'),

    # ── Adresses ─────────────────────────────────────────────────────────────
    path('adresses/',                    views.adresses_list,      name='adresses'),
    path('adresses/<int:pk>/',           views.adresse_detail,     name='adresse_detail'),
    path('adresses/<int:pk>/default/',   views.adresse_set_default, name='adresse_default'),

    # ── Commandes acheteur ───────────────────────────────────────────────────
    path('commandes/',                views.acheteur_commandes,       name='acheteur_commandes'),
    path('commandes/<str:numero>/',   views.acheteur_commande_detail, name='acheteur_commande_detail'),

    # ── Dashboard Producteur ─────────────────────────────────────────────────
    path('producteur/stats/',                             views.producteur_stats,            name='producteur_stats'),
    path('producteur/profil/',                            views.producteur_profil,           name='producteur_profil'),
    path('producteur/commandes/',                         views.producteur_commandes,        name='producteur_commandes'),
    path('producteur/commandes/<str:numero>/',            views.producteur_commande_detail,  name='producteur_commande_detail'),
    path('producteur/commandes/<str:numero>/statut/',     views.producteur_commande_statut,  name='producteur_commande_statut'),
]
