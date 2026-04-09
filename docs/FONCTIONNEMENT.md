# Makèt Peyizan — Documentation Fonctionnelle

> Marketplace agricole haïtienne connectant producteurs et acheteurs directement.

---

## Vue d'ensemble

**Makèt Peyizan** est une plateforme e-commerce agricole dédiée à Haïti. Elle permet aux agriculteurs (producteurs) de vendre leurs produits directement à des acheteurs (particuliers, grossistes, restaurants, institutions, coopératives) sans intermédiaire.

**Stack technique :**
- Backend : Django 4 + Django REST Framework
- Base de données : PostgreSQL
- Auth : JWT (SimpleJWT avec blacklist)
- Paiements : MonCash, NatCash, cash, virement, vouchers
- Notifications : Firebase Cloud Messaging (FCM)
- Emails : Resend API
- Docs API : OpenAPI/Swagger (`/api/schema/swagger-ui/`)
- Admin UI : Jazzmin (Django Admin amélioré)

**Couverture géographique :** Les 10 départements d'Haïti.

---

## Rôles utilisateurs

| Rôle | Description | Accès |
|------|-------------|-------|
| `superadmin` | Administrateur plateforme | Tout |
| `producteur` | Agriculteur/vendeur | Gestion produits, commandes reçues, stock |
| `acheteur` | Client/acheteur | Catalogue, panier, commandes |
| `collecteur` | Agent de collecte logistique | Suivi des tournées de collecte |

---

## Récit utilisateur — SUPERADMIN

L'administrateur supervise l'ensemble de la plateforme via l'API admin (`/api/admin/*`) et l'interface Django Admin (`/admin/`).

### Gestion des utilisateurs
1. Consulter la liste de tous les utilisateurs (`GET /api/admin/users/`)
2. Voir le profil complet d'un utilisateur (`GET /api/admin/users/<id>/detail/`)
3. Activer ou désactiver un compte (`PATCH /api/admin/users/<id>/toggle/`)

### Validation des producteurs
1. Consulter les producteurs en attente de validation (`GET /api/admin/producteurs/`)
2. Voir le dossier d'un producteur (infos, photo CNI, localisation)
3. Approuver, rejeter ou suspendre un producteur (`PATCH /api/admin/producteurs/<id>/statut/`)
   - Un producteur **doit être approuvé** avant de pouvoir publier des produits

### Gestion du catalogue
1. Voir tous les produits de la plateforme (`GET /api/admin/catalogue/`)
2. Activer, désactiver ou archiver un produit (`PATCH /api/admin/catalogue/<id>/statut/`)
3. Créer un produit au nom d'un producteur (`POST /api/admin/catalogue/create/`)

### Gestion des commandes
1. Voir toutes les commandes (`GET /api/admin/commandes/`)
2. Changer le statut d'une commande (`PATCH /api/admin/commandes/<numero>/statut/`)
3. Suivre le statut de paiement et les preuves de paiement

### Vérification des paiements
1. Lister tous les paiements (`GET /api/admin/paiements/`)
2. Vérifier ou rejeter un paiement (`PATCH /api/admin/paiements/<id>/statut/`)
3. Suivre les preuves soumises par les acheteurs

### Gestion du stock
1. Consulter tous les lots (`GET /api/admin/stocks/lots/`)
2. Créer un lot de stock (`POST /api/admin/stocks/lots/create/`)
3. Consulter les alertes de stock faible (`GET /api/admin/stocks/alertes/`)
4. Suivre les mouvements de stock (`GET /api/admin/stocks/mouvements/`)

### Logistique (Collectes)
1. Planifier une collecte (tournée de ramassage) (`POST /api/admin/collectes/create/`)
2. Assigner un collecteur à une zone
3. Suivre le cycle : `PLANIFIÉE → EN_COURS → TERMINÉE`
4. Voir la participation des producteurs et les quantités réelles collectées

### Vouchers / Bons de réduction
1. Créer un programme de vouchers (ONG, gouvernement, coopérative, entreprise)
2. Émettre des codes vouchers pour des bénéficiaires (`POST /api/admin/vouchers/`)
3. Définir la valeur (fixe ou %) et les contraintes (montant min, catégories, expiration)
4. Suivre l'utilisation et le budget restant

### Configuration du site
1. Modifier les informations de branding, logo, slogan (`PATCH /api/admin/config/site/`)
2. Gérer les slides de la page d'accueil
3. Gérer le contenu FAQ (`/api/admin/config/faq/*`)
4. Consulter et répondre aux messages de contact
5. Activer/désactiver le mode maintenance

### Analytics
- Tableau de bord global (`GET /api/admin/stats/`) : utilisateurs, revenus, commandes, produits actifs
- Dashboard BI interactif (`/analytics/dashboard/`)

---

## Récit utilisateur — PRODUCTEUR

Le producteur est un agriculteur qui vend ses produits sur la plateforme. Son compte doit être **validé par l'admin** avant de pouvoir publier.

### Inscription et validation
1. S'inscrire avec `role='producteur'` (`POST /api/auth/register/`)
2. Compléter le profil : département, commune, superficie, photo CNI
3. Attendre la **validation admin** (statut : `EN_ATTENTE → ACTIF`)
4. Recevoir un code producteur unique (ex: `PROD-2026-0042`)

### Gestion des produits
1. Créer un produit (`POST /api/products/mes-produits/`)
   - Nom, description, prix unitaire, prix de gros, catégorie, unité de vente
   - Un **QR code** est automatiquement généré pour chaque produit
   - Un **slug unique** est auto-généré pour l'URL publique
2. Voir et gérer ses produits (`GET /api/products/mes-produits/`)
3. Modifier un produit (`PATCH /api/products/mes-produits/<slug>/`)
4. Statuts produit : `BROUILLON → EN_ATTENTE → ACTIF → ÉPUISÉ / INACTIF`

### Gestion du stock (Lots)
1. Créer un lot (une récolte) : quantité, date de récolte, date d'expiration
2. Le stock disponible du produit est **synchronisé automatiquement** avec les lots actifs
3. Recevoir des alertes quand le stock passe sous le seuil configuré
4. Unités de vente disponibles : kg, tonne, sac 50kg, sac 25kg, botte, pièce, litre, carton, douzaine

### Gestion des commandes reçues
1. Consulter les commandes reçues (`GET /api/auth/producteur/commandes/`)
2. Mettre à jour le statut d'une commande (`PATCH /api/auth/producteur/commandes/<numero>/statut/`)

**Cycle de vie d'une commande côté producteur :**
```
EN_ATTENTE → CONFIRMÉE → EN_PRÉPARATION → PRÊTE → EN_COLLECTE → LIVRÉE
```

### Tableau de bord
`GET /api/auth/producteur/stats/` retourne :
- Revenus total et du mois en cours
- Nombre de commandes par statut
- Nombre de produits actifs et expirés
- Alertes de stock faibles
- Prochains événements de collecte

### Participation aux collectes
1. Voir les événements de collecte planifiés dans sa zone
2. S'inscrire à une collecte (exprimer son intérêt, estimer les quantités)
3. Confirmer sa participation
4. Faire remonter les quantités réelles lors de la collecte

---

## Récit utilisateur — ACHETEUR

L'acheteur peut être un particulier, grossiste, détaillant, coopérative, institution ou restaurant. Son inscription est **immédiate**, sans validation requise.

### Inscription et profil
1. S'inscrire avec `role='acheteur'` (`POST /api/auth/register/`)
2. Compléter le profil : type d'acheteur, nom d'organisation (si applicable)
3. Ajouter et gérer ses adresses de livraison (`POST /api/auth/adresses/`)

### Découverte du catalogue
1. Parcourir tous les produits (`GET /api/products/`) — **public, sans connexion**
2. Filtrer par catégorie, département, fourchette de prix, producteur
3. Voir le détail d'un produit avec galerie photos (`GET /api/products/public/<slug>/`)
4. Consulter les catégories disponibles (`GET /api/products/categories/`)

### Panier d'achat (Panier persistant)
1. Ajouter un produit au panier (`POST /api/orders/panier/ajouter/`)
2. Voir son panier (`GET /api/orders/panier/`)
3. Modifier la quantité d'un article (`PATCH /api/orders/panier/modifier/<slug>/`)
4. Retirer un article (`DELETE /api/orders/panier/retirer/<slug>/`)
5. Vider le panier (`POST /api/orders/panier/vider/`)

> Le panier est **persistant** — il est sauvegardé même après déconnexion.

### Passer une commande (Checkout)
1. Initier la commande (`POST /api/orders/commander/`) avec :
   - Méthode de paiement : `moncash`, `natcash`, `virement`, `cash`, `voucher`, `hors_ligne`
   - Mode de livraison : `domicile`, `retrait`, `collecte`
   - Adresse de livraison
   - Notes éventuelles
2. Le système **crée automatiquement une commande par producteur** (si achat chez plusieurs producteurs)
3. Chaque commande reçoit un numéro unique (ex: `CMD-2026-00123`)

### Suivi des commandes
1. Voir toutes ses commandes (`GET /api/auth/commandes/`)
2. Voir le détail d'une commande (`GET /api/auth/commandes/<numero>/`)

**Cycle de vie d'une commande :**
```
EN_ATTENTE → CONFIRMÉE → EN_PRÉPARATION → PRÊTE → EN_COLLECTE → LIVRÉE
                                                              ↘ ANNULÉE / LITIGE
```

### Paiement
- **MonCash / NatCash** : paiement mobile en temps réel
- **Cash / Hors ligne** : payer à la livraison ou remise en main
- **Virement bancaire** : soumettre une preuve de virement (image)
- **E-Voucher** : saisir un code de réduction (fixe ou %)
- Soumettre la preuve de paiement → l'admin vérifie et confirme

### Utilisation des vouchers
1. Recevoir un code voucher (attribué par l'admin ou un programme)
2. Appliquer le code lors du checkout
3. La réduction est calculée automatiquement (montant fixe ou %)
4. Contraintes : montant minimum de commande, catégories autorisées, date d'expiration

---

## Récit utilisateur — COLLECTEUR

Le collecteur est un agent logistique chargé de récupérer les produits chez les producteurs lors des tournées de collecte.

### Missions
1. Être assigné à une collecte par l'admin
2. Voir les producteurs participants et leurs quantités estimées
3. Mettre à jour le statut de la collecte (`EN_COURS` au démarrage)
4. Enregistrer les quantités réellement collectées chez chaque producteur
5. Clore la collecte (`TERMINÉE`)

---

## Cycle de vie des commandes (vue globale)

```
[ACHETEUR] Ajoute au panier
     ↓
[ACHETEUR] Passe commande (checkout)
     ↓
[SYSTÈME] Crée commande(s) par producteur → statut: EN_ATTENTE
     ↓
[PRODUCTEUR] Confirme → statut: CONFIRMÉE
     ↓
[PRODUCTEUR] Prépare → statut: EN_PRÉPARATION
     ↓
[PRODUCTEUR] Prête → statut: PRÊTE
     ↓
[COLLECTEUR/LIVRAISON] → statut: EN_COLLECTE
     ↓
[ADMIN/PRODUCTEUR] Livraison confirmée → statut: LIVRÉE
```

---

## Structure des URLs

```
/api/auth/              → Authentification & profils
/api/products/          → Catalogue (public + producteur)
/api/orders/            → Panier & commandes
/api/payments/          → Paiements
/api/stock/             → Stock (admin)
/api/collectes/         → Logistique collectes
/api/geo/               → Données géographiques (départements, communes)
/api/admin/             → Toutes les fonctions admin
/admin/                 → Interface Django Admin (Jazzmin)
/analytics/             → Dashboard analytique
/api/schema/swagger-ui/ → Documentation API interactive
/faq/                   → FAQ publique
/contact/               → Formulaire de contact public
/health/                → Health check
```

---

## Sécurité & Authentification

- **JWT** : token `access` (1 jour) + token `refresh` (30 jours)
- En-tête : `Authorization: Bearer <access_token>`
- Refresh : `POST /api/auth/token/refresh/`
- Logout : blacklist du refresh token (`POST /api/auth/logout/`)
- Support cookie + header (middleware personnalisé)
- Permissions granulaires par rôle :
  - `IsProducteur` — role == 'producteur'
  - `IsProducteurActif` — role == 'producteur' + statut == 'actif'
  - `IsAcheteur` — role == 'acheteur'
  - `IsSuperAdmin` — is_superuser OR is_staff OR role == 'superadmin'

---

## Notifications

- **FCM (Firebase)** : notifications push sur mobile lors des changements de statut
- **Email (Resend)** : confirmations et alertes par email
- Les tokens FCM sont abonnés à des topics par rôle (`role_acheteur`, `role_producteur`)
- Déconnexion = désabonnement automatique de tous les topics

---

## Données géographiques

Couverture complète des 10 départements haïtiens :
Ouest, Sud-Est, Nord, Nord-Est, Artibonite, Centre, Sud, Grand-Anse, Nord-Ouest, Nippes.

Chaque producteur est localisé par département et commune.
Les collectes sont organisées par zones géographiques.
