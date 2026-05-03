from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import CustomUser, Producteur
from apps.catalog.models import Categorie, Produit


def _setup_catalog():
    user = CustomUser.objects.create_user(
        username='producteur_catalog',
        email='prod_catalog@test.com',
        password='Testpass123!',
        role='producteur',
    )
    prod = Producteur.objects.create(
        user=user,
        departement='ouest',
        commune='Port-au-Prince',
        statut='actif',
    )
    cat = Categorie.objects.create(
        nom='Légumes',
        slug='legumes',
        is_active=True,
    )
    return prod, cat


class ProduitListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.prod, self.cat = _setup_catalog()
        self.produit = Produit.objects.create(
            producteur=self.prod,
            categorie=self.cat,
            nom='Carotte fraîche',
            slug='carotte-fraiche',
            prix_unitaire='150.00',
            unite_vente='kg',
            stock_disponible=50,
            statut='actif',
            is_active=True,
        )

    def test_list_produits_public(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['count'], 1)

    def test_list_produits_filter_categorie(self):
        response = self.client.get('/api/products/?categorie=legumes')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

    def test_list_produits_filter_categorie_inexistante(self):
        response = self.client.get('/api/products/?categorie=zzz-inexistante')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)

    def test_produit_inactif_absent_de_la_liste(self):
        self.produit.is_active = False
        self.produit.save()
        response = self.client.get('/api/products/')
        self.assertEqual(response.data['data']['count'], 0)

    def test_produit_stock_zero_absent_de_la_liste(self):
        self.produit.stock_disponible = 0
        self.produit.save()
        response = self.client.get('/api/products/')
        self.assertEqual(response.data['data']['count'], 0)

    def test_produit_detail_public(self):
        response = self.client.get(f'/api/products/public/{self.produit.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['nom'], 'Carotte fraîche')

    def test_produit_detail_inexistant_404(self):
        response = self.client.get('/api/products/public/produit-inexistant/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CategorieListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Categorie.objects.create(nom='Fruits', slug='fruits', is_active=True)
        Categorie.objects.create(nom='Inactive', slug='inactive', is_active=False)

    def test_categories_list_active_only(self):
        response = self.client.get('/api/products/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        noms = [c['nom'] for c in response.data['data']]
        self.assertIn('Fruits', noms)
        self.assertNotIn('Inactive', noms)
