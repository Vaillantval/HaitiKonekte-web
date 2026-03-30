from django.urls import path
from .views import DashboardView, ExportDashboardView, carte_utilisateurs

app_name = 'analytics'
urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('export/', ExportDashboardView.as_view(), name='export'),
    path('carte/', carte_utilisateurs, name='carte_users'),
]
