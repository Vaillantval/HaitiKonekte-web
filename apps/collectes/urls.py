from django.urls import path
from apps.collectes import views

app_name = 'collectes'

urlpatterns = [
    path(
        'mes-participations/',
        views.mes_participations,
        name='mes_participations',
    ),
    path(
        'participations/<int:pk>/confirmer/',
        views.confirmer_participation,
        name='confirmer_participation',
    ),
]
