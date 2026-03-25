from django.urls import path
from apps.collectes.views import MesParticipationsView, ParticipationConfirmerView

app_name = 'collectes'

urlpatterns = [
    path('mes-participations/',                              MesParticipationsView.as_view(),    name='mes_participations'),
    path('participations/<int:pk>/confirmer/',               ParticipationConfirmerView.as_view(), name='participation_confirmer'),
]
