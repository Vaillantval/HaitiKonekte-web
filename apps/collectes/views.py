from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.collectes.models import ParticipationCollecte


class MesParticipationsView(APIView):
    """Liste les participations collecte du producteur connecté."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            producteur = request.user.profil_producteur
        except Exception:
            return Response({'detail': 'Compte producteur introuvable.'}, status=403)

        qs = (
            ParticipationCollecte.objects
            .filter(producteur=producteur)
            .select_related('collecte', 'collecte__zone', 'collecte__point_collecte')
            .order_by('-collecte__date_planifiee')
        )

        data = []
        for p in qs:
            c = p.collecte
            data.append({
                'id':               p.pk,
                'statut':           p.statut,
                'statut_label':     p.get_statut_display(),
                'quantite_prevue':  p.quantite_prevue,
                'quantite_collectee': p.quantite_collectee,
                'notes':            p.notes,
                'created_at':       p.created_at.isoformat(),
                'collecte': {
                    'id':            c.pk,
                    'reference':     c.reference,
                    'statut':        c.statut,
                    'statut_label':  c.get_statut_display(),
                    'date_planifiee': str(c.date_planifiee),
                    'heure_debut':   str(c.heure_debut) if c.heure_debut else None,
                    'zone':          c.zone.nom,
                    'departement':   c.zone.get_departement_display(),
                    'point':         c.point_collecte.nom if c.point_collecte else None,
                    'commune':       c.point_collecte.commune if c.point_collecte else None,
                    'notes':         c.notes,
                },
            })

        return Response(data)


class ParticipationConfirmerView(APIView):
    """
    Le producteur confirme sa participation à une collecte (accuse de reception).
    PATCH /api/collectes/participations/<pk>/confirmer/
    Body optionnel : { "quantite_prevue": int, "notes": str }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            producteur = request.user.profil_producteur
        except Exception:
            return Response({'detail': 'Compte producteur introuvable.'}, status=403)

        try:
            participation = ParticipationCollecte.objects.select_related(
                'collecte', 'collecte__zone', 'producteur', 'producteur__user'
            ).get(pk=pk, producteur=producteur)
        except ParticipationCollecte.DoesNotExist:
            return Response({'detail': 'Participation introuvable.'}, status=404)

        if participation.statut != ParticipationCollecte.Statut.INSCRIT:
            return Response(
                {'detail': f'Déjà traitée (statut : {participation.get_statut_display()}).'},
                status=400
            )

        # Mettre à jour
        quantite = request.data.get('quantite_prevue')
        notes    = request.data.get('notes', '').strip()

        if quantite is not None:
            try:
                participation.quantite_prevue = int(quantite)
            except (ValueError, TypeError):
                pass

        if notes:
            participation.notes = notes

        participation.statut = ParticipationCollecte.Statut.CONFIRME
        participation.save(update_fields=['statut', 'quantite_prevue', 'notes', 'updated_at'])

        # Notifier les admins
        try:
            from apps.emails.utils import email_collecte_confirme_admin
            from apps.emails.fcm_notifications import push_collecte_confirmee_admin
            email_collecte_confirme_admin(participation)
            push_collecte_confirmee_admin(participation)
        except Exception:
            pass  # Ne pas bloquer si notifications échouent

        return Response({
            'detail':       'Participation confirmée.',
            'statut':       participation.statut,
            'statut_label': participation.get_statut_display(),
        })
