from django.test import TestCase, RequestFactory
from unittest.mock import MagicMock

from apps.accounts.models import CustomUser, Producteur, Acheteur
from apps.catalog.models import Categorie, Produit
from apps.orders.services.cart_service import CartService


def _make_produit():
    user = CustomUser.objects.create_user(
        username='prod_orders',
        email='prod_orders@test.com',
        password='Testpass123!',
        role='producteur',
    )
    prod = Producteur.objects.create(
        user=user, departement='ouest', commune='Port-au-Prince', statut='actif',
    )
    cat = Categorie.objects.create(nom='Légumes', slug='legumes-orders', is_active=True)
    return Produit.objects.create(
        producteur=prod,
        categorie=cat,
        nom='Patate douce',
        slug='patate-douce',
        prix_unitaire='100.00',
        unite_vente='kg',
        stock_disponible=100,
        statut='actif',
        is_active=True,
    )


class CartSessionTests(TestCase):
    """Tests du panier en mode session (utilisateur anonyme)."""

    def _anon_request(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        request.session = {}
        return request

    def setUp(self):
        self.produit = _make_produit()

    def test_ajouter_produit(self):
        request = self._anon_request()
        resume = CartService.ajouter(request, self.produit, quantite=2)
        self.assertEqual(resume['nb_articles'], 2)
        self.assertEqual(resume['nb_items'], 1)

    def test_ajouter_meme_produit_cumule(self):
        request = self._anon_request()
        CartService.ajouter(request, self.produit, quantite=1)
        resume = CartService.ajouter(request, self.produit, quantite=3)
        self.assertEqual(resume['nb_articles'], 4)

    def test_retirer_produit(self):
        request = self._anon_request()
        CartService.ajouter(request, self.produit, quantite=2)
        resume = CartService.retirer(request, self.produit.slug)
        self.assertEqual(resume['nb_articles'], 0)

    def test_modifier_quantite(self):
        request = self._anon_request()
        CartService.ajouter(request, self.produit, quantite=5)
        resume = CartService.modifier_quantite(request, self.produit.slug, 2)
        self.assertEqual(resume['nb_articles'], 2)

    def test_modifier_quantite_zero_retire(self):
        request = self._anon_request()
        CartService.ajouter(request, self.produit, quantite=3)
        resume = CartService.modifier_quantite(request, self.produit.slug, 0)
        self.assertEqual(resume['nb_articles'], 0)

    def test_vider_panier(self):
        request = self._anon_request()
        CartService.ajouter(request, self.produit, quantite=2)
        CartService.vider(request)
        self.assertEqual(CartService.nb_articles(request), 0)

    def test_contient_vrai(self):
        request = self._anon_request()
        CartService.ajouter(request, self.produit, quantite=1)
        self.assertTrue(CartService.contient(request, self.produit.slug))

    def test_contient_faux(self):
        request = self._anon_request()
        self.assertFalse(CartService.contient(request, self.produit.slug))

    def test_total_calcule(self):
        request = self._anon_request()
        resume = CartService.ajouter(request, self.produit, quantite=3)
        expected = float(self.produit.prix_unitaire) * 3
        self.assertAlmostEqual(resume['total'], expected, places=2)


class CartDBTests(TestCase):
    """Tests du panier en mode DB (utilisateur authentifié)."""

    def _auth_request(self, user):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user
        return request

    def setUp(self):
        self.produit = _make_produit()
        self.buyer = CustomUser.objects.create_user(
            username='acheteur_cart',
            email='buyer@test.com',
            password='Testpass123!',
            role='acheteur',
        )
        Acheteur.objects.create(user=self.buyer)

    def test_ajouter_db(self):
        request = self._auth_request(self.buyer)
        resume = CartService.ajouter(request, self.produit, quantite=2)
        self.assertEqual(resume['nb_articles'], 2)

    def test_retirer_db(self):
        request = self._auth_request(self.buyer)
        CartService.ajouter(request, self.produit, quantite=2)
        resume = CartService.retirer(request, self.produit.slug)
        self.assertEqual(resume['nb_articles'], 0)

    def test_vider_db(self):
        request = self._auth_request(self.buyer)
        CartService.ajouter(request, self.produit, quantite=3)
        CartService.vider(request)
        self.assertEqual(CartService.nb_articles(request), 0)
