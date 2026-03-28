# Recommandations Flutter — Makèt Peyizan Mobile

> Guide technique pour reproduire les fonctionnalités de la plateforme web Makèt Peyizan dans une application Flutter, en se basant sur l'API REST existante.

---

## Stack recommandée

| Besoin | Package Flutter |
|--------|----------------|
| Requêtes HTTP + JWT | `dio` + `dio_cookie_manager` |
| Persistance locale | `flutter_secure_storage` (tokens) + `shared_preferences` (préfs) |
| Gestion d'état | `riverpod` ou `bloc` |
| Navigation | `go_router` |
| Images réseau | `cached_network_image` |
| Push notifications | `firebase_messaging` |
| Internationalisation | `flutter_localizations` (français par défaut) |
| Paiement MonCash | `webview_flutter` (redirect URL MonCash) |
| Upload fichiers | `image_picker` + `dio` multipart |

---

## 1. Authentification JWT

### Implémentation recommandée

```dart
// auth_service.dart
class AuthService {
  final Dio _dio;

  Future<AuthResponse> login(String email, String password) async {
    final res = await _dio.post('/api/auth/login/', data: {
      'email': email, 'password': password,
    });
    // Stocker dans flutter_secure_storage
    await storage.write(key: 'access', value: res.data['access']);
    await storage.write(key: 'refresh', value: res.data['refresh']);
    return AuthResponse.fromJson(res.data);
  }
}
```

### Intercepteur de token

```dart
// Ajoute automatiquement le header Authorization à chaque requête
// et rafraîchit le token si 401 reçu
dio.interceptors.add(InterceptorsWrapper(
  onRequest: (options, handler) async {
    final token = await storage.read(key: 'access');
    options.headers['Authorization'] = 'Bearer $token';
    handler.next(options);
  },
  onError: (error, handler) async {
    if (error.response?.statusCode == 401) {
      // Rafraîchir via POST /api/auth/token/refresh/
      // Puis relancer la requête originale
    }
    handler.next(error);
  },
));
```

### Redirections post-login (même logique que le web)
- `role == 'superadmin'` ou `is_superuser` → écran Admin Dashboard
- `role == 'producteur'` → écran Producteur Dashboard
- `role == 'acheteur'` → écran Accueil (catalogue)
- `role == 'collecteur'` → écran Collectes

---

## 2. Catalogue & Recherche

### Liste avec infinite scroll

```dart
// GET /api/products/?page=1&page_size=20&search=banane&categorie=fruits
Future<CataloguePage> fetchCatalogue({
  int page = 1,
  String? search,
  String? categorieSlug,
  String? departement,
  double? prixMin,
  double? prixMax,
}) async {
  final res = await _dio.get('/api/products/', queryParameters: {
    'page': page,
    'page_size': 20,
    if (search != null) 'search': search,
    if (categorieSlug != null) 'categorie': categorieSlug,
    // ...
  });
  return CataloguePage.fromJson(res.data);
}
```

Le champ `next` dans la réponse permet de savoir s'il y a une page suivante pour l'infinite scroll (`ListView.builder` + `ScrollController`).

### Détail produit
```
GET /api/products/public/<slug>/
```
Retourne `similaires` → afficher une section "Vous aimerez aussi".

---

## 3. Panier (DB-backed pour utilisateurs connectés)

Le panier est **persistant en base de données** pour tout utilisateur avec un JWT valide. Pas besoin de gérer un panier local dans Flutter.

```dart
// Ajouter au panier
await _dio.post('/api/orders/panier/ajouter/', data: {
  'slug': produit.slug,
  'quantite': 2,
});

// Récupérer le panier
final res = await _dio.get('/api/orders/panier/');
// res.data['items'], res.data['total'], res.data['nb_articles']

// Modifier quantité
await _dio.patch('/api/orders/panier/modifier/$slug/', data: {'quantite': 3});

// Retirer un article
await _dio.delete('/api/orders/panier/retirer/$slug/');

// Vider
await _dio.delete('/api/orders/panier/vider/');
```

Le badge panier dans la navbar = `res.data['nb_articles']`.

---

## 4. Passer commande

### Flux normal (cash / hors ligne)
```dart
await _dio.post('/api/orders/commander/', data: {
  'methode_paiement': 'cash',
  'mode_livraison': 'domicile',
  'adresse_livraison_id': adresseId,   // ou adresse_livraison_text
  'notes': 'Livrer avant midi',
});
```

### Flux MonCash
```dart
final res = await _dio.post('/api/orders/commander/', data: {
  'methode_paiement': 'moncash',
  // ...
});
// Ouvrir la redirect_url dans un WebView
final redirectUrl = res.data['redirect_url'];
// Utiliser webview_flutter pour laisser l'utilisateur payer sur MonCash
// Après paiement, MonCash redirige vers /commander/moncash/retour/
```

### Preuve de paiement (hors ligne)
```dart
// multipart/form-data avec image
final formData = FormData.fromMap({
  'methode_paiement': 'hors_ligne',
  'preuve_paiement': await MultipartFile.fromFile(imagePath),
  // ...
});
await _dio.post('/api/orders/commander/', data: formData);
```

---

## 5. Profil & Adresses

### Mise à jour profil avec photo
```dart
// PATCH /api/auth/me/ en multipart
final formData = FormData.fromMap({
  'first_name': 'Jean',
  'last_name': 'Dupont',
  'telephone': '+50912345678',
  if (photoPath != null)
    'photo': await MultipartFile.fromFile(photoPath),
});
await _dio.patch('/api/auth/me/', data: formData);
```

### Gestion adresses
CRUD complet via `/api/auth/adresses/`. Afficher un sélecteur géographique cascade :
1. `GET /api/geo/departements/`
2. `GET /api/geo/communes/?dept=<slug>`
3. `GET /api/geo/sections/?dept=<slug>&commune=<nom>`

---

## 6. Push Notifications (Firebase)

### Enregistrement du device

```dart
// Après login, enregistrer le token FCM
final fcmToken = await FirebaseMessaging.instance.getToken();
await _dio.post('/api/auth/fcm-token/', data: {'fcm_token': fcmToken});
```

### Topics par rôle
L'API abonne automatiquement l'utilisateur à son topic de rôle :
- `role_acheteur` — nouvelles commandes, promotions
- `role_producteur` — nouvelles commandes reçues, alertes stock
- `role_collecteur` — nouvelles collectes planifiées
- `role_superadmin` — alertes critiques

### Gestion des messages reçus
```dart
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  // Afficher une notification in-app (overlay ou snackbar)
});

FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
  // Naviguer vers l'écran approprié selon message.data['type']
});
```

### Déconnexion : se désabonner
```dart
await _dio.post('/api/auth/logout/', data: {
  'refresh': refreshToken,
  'fcm_token': fcmToken,
});
```

---

## 7. Dashboard Producteur

### Écrans à implémenter

| Écran | Endpoint |
|-------|----------|
| Vue d'ensemble | `GET /api/auth/producteur/stats/` |
| Commandes reçues | `GET /api/auth/producteur/commandes/?statut=` |
| Détail commande | `GET /api/auth/producteur/commandes/<numero>/` |
| Changer statut | `PATCH /api/auth/producteur/commandes/<numero>/statut/` |
| Mon catalogue | `GET /api/products/mes-produits/` |
| Ajouter produit | `POST /api/products/mes-produits/` |
| Mes collectes | `GET /api/collectes/mes-participations/` |
| Mon profil | `GET/PATCH /api/auth/producteur/profil/` |

### Statuts commande — actions possibles

| Action | Transition |
|--------|-----------|
| `confirmer` | en_attente → confirmee |
| `preparer` | confirmee → en_preparation |
| `prete` | en_preparation → prete |
| `annuler` | tout → annulee (motif requis) |

---

## 8. Géographie (sélecteur en cascade)

```dart
// Widget réutilisable GeoSelector
class GeoSelector extends StatefulWidget {
  // 1. Charger les départements au démarrage
  // GET /api/geo/departements/

  // 2. Au choix du département, charger les communes
  // GET /api/geo/communes/?dept=<slug>

  // 3. Au choix de la commune, charger les sections
  // GET /api/geo/sections/?dept=<slug>&commune=<nom>
}
```

Mettre en cache le résultat 24h avec `shared_preferences` ou `hive`.

---

## 9. Rôles et navigation

| Rôle | Accès | Navigation principale |
|------|-------|----------------------|
| `acheteur` | Catalogue, panier, commandes, profil | BottomNavigationBar : Accueil, Catalogue, Panier, Commandes, Profil |
| `producteur` | Dashboard producteur | BottomNavigationBar : Dashboard, Commandes, Catalogue, Collectes, Profil |
| `collecteur` | Collectes terrain | BottomNavigationBar : Collectes, Profil |
| `superadmin` | Tout (admin API) | Navigation latérale admin |

---

## 10. Gestion des images

Toutes les images sont servies en relatif (ex: `/media/produits/banane.jpg`).

En Flutter, construire l'URL complète :
```dart
final String baseUrl = 'https://ton-app.up.railway.app';

String imageUrl(String? relativePath) {
  if (relativePath == null || relativePath.isEmpty) return '';
  if (relativePath.startsWith('http')) return relativePath;
  return '$baseUrl$relativePath';
}
```

Utiliser `CachedNetworkImage` pour les performances :
```dart
CachedNetworkImage(
  imageUrl: imageUrl(produit.imagePrincipale),
  placeholder: (ctx, url) => Shimmer(),
  errorWidget: (ctx, url, e) => Icon(Icons.image_not_supported),
)
```

---

## 11. Gestion des erreurs API

```dart
// Intercepteur global pour les erreurs
dio.interceptors.add(InterceptorsWrapper(
  onError: (DioException e, handler) {
    switch (e.response?.statusCode) {
      case 400:
        // Afficher les détails de validation : e.response?.data['detail']
        break;
      case 401:
        // Token expiré → rafraîchir ou rediriger vers login
        break;
      case 403:
        // Accès refusé → snackbar "Permission insuffisante"
        break;
      case 404:
        // Ressource introuvable
        break;
      default:
        // Erreur serveur générique
    }
    handler.next(e);
  },
));
```

---

## 12. Inscription producteur — flux spécial

Après inscription (`POST /api/auth/register/` avec `role='producteur'`), le compte est en attente de validation par le superadmin. Le producteur ne peut pas accéder à son dashboard avant validation.

```dart
// Après inscription producteur :
// → Afficher écran "Compte en attente de validation"
// → Écouter les notifications FCM pour être notifié de l'approbation
// → Vérifier le statut via GET /api/auth/producteur/profil/
//   si profil_producteur.statut == 'actif' → déverrouiller le dashboard
```

---

## Checklist d'implémentation

### Phase 1 — Base
- [ ] Authentification (login, register, logout, refresh token)
- [ ] Catalogue public (listing + filtres + détail)
- [ ] Panier (ajouter, modifier, vider)
- [ ] Passer commande (cash)
- [ ] Profil utilisateur

### Phase 2 — Acheteur complet
- [ ] Mes commandes (liste + détail)
- [ ] Gestion adresses
- [ ] Sélecteur géographique en cascade
- [ ] Paiement MonCash (WebView)
- [ ] Upload preuve de paiement

### Phase 3 — Producteur
- [ ] Dashboard stats
- [ ] Gestion commandes reçues
- [ ] Gestion catalogue produits
- [ ] Mes collectes

### Phase 4 — Notifications & finitions
- [ ] Push FCM (inscription, réception, navigation)
- [ ] Changement de mot de passe
- [ ] Upload photo de profil
- [ ] Mode hors-ligne basique (cache catalogue)
- [ ] Écran inscription producteur avec statut en attente
