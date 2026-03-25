from django.urls import path
from apps.accounts.views_superadmin import (
    AdminStatsView,
    AdminUsersView, AdminUserToggleView, AdminUserCreateView, AdminUserDetailView,
    AdminProducteursView, AdminProducteurStatutView, AdminProducteurCreateView, AdminProducteurDetailView,
    AdminCommandesView, AdminCommandeDetailView, AdminCommandeStatutView,
    AdminPaiementsView, AdminPaiementStatutView,
    AdminCatalogueView, AdminCatalogueToggleView, AdminCatalogueStatutView,
    AdminCatalogueCreateView, AdminCatalogueDetailView,
    AdminStocksLotsView, AdminStocksAlertesView, AdminStockLotCreateView, AdminStockLotDetailView,
    AdminCollectesView, AdminCollecteDetailView, AdminCollecteStatutView,
    AdminCollecteCreateView, AdminCollecteEditView,
    AdminCollecteAddParticipationView,
    AdminParticipationStatutView, AdminParticipationDeleteView,
    AdminOptionsView,
)

urlpatterns = [
    path('stats/',                                            AdminStatsView.as_view(),                    name='admin_stats'),
    path('options/',                                          AdminOptionsView.as_view(),                  name='admin_options'),

    # Utilisateurs
    path('users/',                                            AdminUsersView.as_view(),                    name='admin_users'),
    path('users/create/',                                     AdminUserCreateView.as_view(),               name='admin_user_create'),
    path('users/<int:pk>/toggle/',                            AdminUserToggleView.as_view(),               name='admin_user_toggle'),
    path('users/<int:pk>/detail/',                            AdminUserDetailView.as_view(),               name='admin_user_detail'),

    # Producteurs
    path('producteurs/',                                      AdminProducteursView.as_view(),              name='admin_producteurs'),
    path('producteurs/create/',                               AdminProducteurCreateView.as_view(),         name='admin_producteur_create'),
    path('producteurs/<int:pk>/statut/',                      AdminProducteurStatutView.as_view(),         name='admin_producteur_statut'),
    path('producteurs/<int:pk>/detail/',                      AdminProducteurDetailView.as_view(),         name='admin_producteur_detail'),

    # Commandes
    path('commandes/',                                        AdminCommandesView.as_view(),                name='admin_commandes'),
    path('commandes/<str:numero>/',                           AdminCommandeDetailView.as_view(),           name='admin_commande_detail'),
    path('commandes/<str:numero>/statut/',                    AdminCommandeStatutView.as_view(),           name='admin_commande_statut'),

    # Paiements
    path('paiements/',                                        AdminPaiementsView.as_view(),                name='admin_paiements'),
    path('paiements/<int:pk>/statut/',                        AdminPaiementStatutView.as_view(),           name='admin_paiement_statut'),

    # Catalogue
    path('catalogue/',                                        AdminCatalogueView.as_view(),                name='admin_catalogue'),
    path('catalogue/create/',                                 AdminCatalogueCreateView.as_view(),          name='admin_catalogue_create'),
    path('catalogue/<int:pk>/toggle/',                        AdminCatalogueToggleView.as_view(),          name='admin_catalogue_toggle'),
    path('catalogue/<int:pk>/statut/',                        AdminCatalogueStatutView.as_view(),          name='admin_catalogue_statut'),
    path('catalogue/<int:pk>/detail/',                        AdminCatalogueDetailView.as_view(),          name='admin_catalogue_detail'),

    # Stocks
    path('stocks/lots/',                                      AdminStocksLotsView.as_view(),               name='admin_stocks_lots'),
    path('stocks/lots/create/',                               AdminStockLotCreateView.as_view(),           name='admin_stock_lot_create'),
    path('stocks/lots/<int:pk>/',                             AdminStockLotDetailView.as_view(),           name='admin_stock_lot_detail'),
    path('stocks/alertes/',                                   AdminStocksAlertesView.as_view(),            name='admin_stocks_alertes'),

    # Collectes
    path('collectes/',                                        AdminCollectesView.as_view(),                name='admin_collectes'),
    path('collectes/create/',                                 AdminCollecteCreateView.as_view(),           name='admin_collecte_create'),
    path('collectes/participations/<int:pk>/statut/',         AdminParticipationStatutView.as_view(),      name='admin_participation_statut'),
    path('collectes/participations/<int:pk>/',                AdminParticipationDeleteView.as_view(),      name='admin_participation_delete'),
    path('collectes/<int:pk>/',                               AdminCollecteDetailView.as_view(),           name='admin_collecte_detail'),
    path('collectes/<int:pk>/statut/',                        AdminCollecteStatutView.as_view(),           name='admin_collecte_statut'),
    path('collectes/<int:pk>/edit/',                          AdminCollecteEditView.as_view(),             name='admin_collecte_edit'),
    path('collectes/<int:pk>/participations/',                AdminCollecteAddParticipationView.as_view(), name='admin_collecte_add_participation'),
]
