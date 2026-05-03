from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import CustomUser, Producteur, Acheteur


def _make_user(username='testuser', role='acheteur', password='Testpass123!'):
    user = CustomUser.objects.create_user(
        username=username,
        email=f'{username}@test.com',
        password=password,
        role=role,
        first_name='Test',
        last_name='User',
    )
    if role == 'acheteur':
        Acheteur.objects.create(user=user)
    elif role == 'producteur':
        Producteur.objects.create(
            user=user,
            departement='ouest',
            commune='Port-au-Prince',
        )
    return user


class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/auth/register/'

    def test_register_acheteur_success(self):
        data = {
            'username':   'nouvel_acheteur',
            'email':      'nouvel@test.com',
            'password':   'Testpass123!',
            'password2':  'Testpass123!',
            'first_name': 'Jean',
            'last_name':  'Paul',
            'role':       'acheteur',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertTrue(CustomUser.objects.filter(username='nouvel_acheteur').exists())

    def test_register_duplicate_username_fails(self):
        _make_user('existing')
        data = {
            'username':  'existing',
            'email':     'other@test.com',
            'password':  'Testpass123!',
            'password2': 'Testpass123!',
            'role':      'acheteur',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields_fails(self):
        response = self.client.post(self.url, {'username': 'x'}, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/auth/login/'
        self.user = _make_user('loginuser', password='Testpass123!')

    def test_login_success(self):
        response = self.client.post(
            self.url,
            {'email': 'loginuser@test.com', 'password': 'Testpass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['data'])

    def test_login_wrong_password(self):
        response = self.client.post(
            self.url,
            {'email': 'loginuser@test.com', 'password': 'wrongpassword'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unknown_user(self):
        response = self.client.post(
            self.url,
            {'email': 'nobody@test.com', 'password': 'Testpass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = _make_user('meuser')

    def _auth(self):
        response = self.client.post(
            '/api/auth/login/',
            {'email': 'meuser@test.com', 'password': 'Testpass123!'},
            format='json',
        )
        token = response.data['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_me_requires_auth(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_profile(self):
        self._auth()
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['username'], 'meuser')

    def test_change_password_wrong_current(self):
        self._auth()
        response = self.client.post(
            '/api/auth/change-password/',
            {'current_password': 'wrongpassword', 'new_password': 'Newpass456!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AdresseTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = _make_user('adresseuser')
        response = self.client.post(
            '/api/auth/login/',
            {'email': 'adresseuser@test.com', 'password': 'Testpass123!'},
            format='json',
        )
        token = response.data['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_create_and_list_adresse(self):
        payload = {
            'libelle':       'Domicile',
            'nom_complet':   'Jean Paul',
            'telephone':     '50912345678',
            'rue':           '12 Rue des Fleurs',
            'commune':       'Pétionville',
            'departement':   'ouest',
            'type_adresse':  'livraison',
        }
        response = self.client.post('/api/auth/adresses/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        list_response = self.client.get('/api/auth/adresses/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data['data']), 1)
