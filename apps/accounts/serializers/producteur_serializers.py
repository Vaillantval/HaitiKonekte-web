from rest_framework import serializers
from apps.accounts.models import Producteur
from apps.orders.models import Commande


class ProducteurProfilSerializer(serializers.ModelSerializer):
    """Profil boutique d'un producteur (lecture + mise à jour partielle)."""
    nom_complet       = serializers.SerializerMethodField()
    first_name        = serializers.SerializerMethodField()
    last_name         = serializers.SerializerMethodField()
    email             = serializers.SerializerMethodField()
    telephone         = serializers.SerializerMethodField()
    photo             = serializers.SerializerMethodField()
    nb_produits       = serializers.SerializerMethodField()
    nb_commandes      = serializers.SerializerMethodField()
    statut_label      = serializers.CharField(source='get_statut_display',      read_only=True)
    departement_label = serializers.CharField(source='get_departement_display', read_only=True)

    class Meta:
        model  = Producteur
        fields = [
            'id', 'code_producteur', 'nom_complet', 'first_name', 'last_name',
            'email', 'telephone', 'photo',
            'departement', 'departement_label',
            'commune', 'localite', 'adresse_complete', 'superficie_ha',
            'description', 'num_identification',
            'statut', 'statut_label', 'note_admin', 'date_validation',
            'nb_produits', 'nb_commandes', 'created_at',
        ]
        read_only_fields = [
            'id', 'code_producteur', 'statut', 'created_at', 'date_validation',
        ]

    def get_nom_complet(self, obj):
        return obj.user.get_full_name()

    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_email(self, obj):
        return obj.user.email

    def get_telephone(self, obj):
        return obj.user.telephone

    def get_photo(self, obj):
        if obj.user.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.photo.url)
            return obj.user.photo.url
        return None

    def get_nb_produits(self, obj):
        return obj.produits.filter(is_active=True).count()

    def get_nb_commandes(self, obj):
        return Commande.objects.filter(producteur=obj).count()


class ProducteurStatsSerializer(serializers.Serializer):
    """Statistiques du dashboard producteur."""
    commandes_en_attente  = serializers.IntegerField()
    commandes_confirmees  = serializers.IntegerField()
    commandes_en_cours    = serializers.IntegerField()
    commandes_livrees     = serializers.IntegerField()
    commandes_total       = serializers.IntegerField()
    revenus_total         = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenus_mois          = serializers.DecimalField(max_digits=12, decimal_places=2)
    nb_produits_actifs    = serializers.IntegerField()
    nb_produits_epuises   = serializers.IntegerField()
    alertes_stock         = serializers.IntegerField()
    stock_faible          = serializers.IntegerField()
    collectes_a_venir     = serializers.IntegerField()
    statut                = serializers.CharField()
    statut_label          = serializers.CharField()


class CommandeProducteurSerializer(serializers.ModelSerializer):
    """Commande vue depuis le dashboard producteur ou acheteur."""
    acheteur_nom           = serializers.SerializerMethodField()
    acheteur_tel           = serializers.SerializerMethodField()
    acheteur_email         = serializers.SerializerMethodField()
    producteur_nom         = serializers.SerializerMethodField()
    producteur_commune     = serializers.SerializerMethodField()
    statut_label           = serializers.CharField(source='get_statut_display',          read_only=True)
    paiement_label         = serializers.CharField(source='get_statut_paiement_display', read_only=True)
    methode_paiement_label = serializers.CharField(source='get_methode_paiement_display', read_only=True)
    actions_possibles      = serializers.SerializerMethodField()
    details                = serializers.SerializerMethodField()
    preuve_paiement        = serializers.SerializerMethodField()

    class Meta:
        model  = Commande
        fields = [
            'numero_commande',
            'acheteur_nom', 'acheteur_tel', 'acheteur_email',
            'producteur_nom', 'producteur_commune',
            'sous_total', 'frais_livraison', 'remise', 'total',
            'statut', 'statut_label',
            'statut_paiement', 'paiement_label',
            'methode_paiement', 'methode_paiement_label',
            'mode_livraison', 'adresse_livraison',
            'ville_livraison', 'departement_livraison',
            'notes_acheteur', 'date_confirmation',
            'date_livraison_prevue', 'created_at',
            'actions_possibles', 'details', 'preuve_paiement',
        ]

    def get_acheteur_nom(self, obj):
        return obj.acheteur.user.get_full_name()

    def get_acheteur_tel(self, obj):
        return obj.acheteur.user.telephone

    def get_acheteur_email(self, obj):
        return obj.acheteur.user.email

    def get_producteur_nom(self, obj):
        return obj.producteur.user.get_full_name()

    def get_producteur_commune(self, obj):
        return obj.producteur.commune

    def get_actions_possibles(self, obj):
        mapping = {
            'en_attente':     ['confirmer', 'annuler'],
            'confirmee':      ['preparer',  'annuler'],
            'en_preparation': ['prete',     'annuler'],
            'prete':          [],
            'en_collecte':    [],
        }
        return mapping.get(obj.statut, [])

    def get_details(self, obj):
        return [
            {
                'produit':       d.produit.nom,
                'slug':          d.produit.slug,
                'quantite':      d.quantite,
                'unite_vente':   d.unite_vente,
                'prix_unitaire': str(d.prix_unitaire),
                'sous_total':    str(d.sous_total),
            }
            for d in obj.details.select_related('produit').all()
        ]

    def get_preuve_paiement(self, obj):
        request = self.context.get('request')

        def build_url(field):
            if request:
                return request.build_absolute_uri(field.url)
            return field.url

        # Priorité 1 : Commande.preuve_paiement
        if obj.preuve_paiement:
            return build_url(obj.preuve_paiement)

        # Priorité 2 : Paiement.preuve_image lié à la commande
        paiement = obj.paiements.filter(preuve_image__isnull=False).first()
        if paiement and paiement.preuve_image:
            return build_url(paiement.preuve_image)

        return None
