# Makèt Peyizan — Endpoints Paiement pour Flutter

> **Prompt d'intégration** — Ce document décrit tous les endpoints liés au paiement et à la commande pour l'app Flutter. Tous les appels doivent porter le token JWT dans le header `Authorization`.

---

## Authentification requise

Tous les endpoints paiement et commande exigent un utilisateur connecté **avec le rôle `acheteur`**.

```
Header: Authorization: Bearer <access_token>
```

Le token s'obtient via :

```
POST /api/auth/login/
Body: { "email": "...", "password": "..." }
Response: { "data": { "access": "...", "refresh": "...", "user": { "role": "acheteur", ... } } }
```

---

## 1. Passer commande (checkout)

```
POST /api/orders/commander/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

| Champ | Type | Requis | Valeurs |
|---|---|---|---|
| `methode_paiement` | string | oui | `"cash"` \| `"moncash"` \| `"natcash"` \| `"hors_ligne"` |
| `mode_livraison` | string | oui | `"domicile"` \| `"collecte"` \| `"retrait"` |
| `adresse_livraison_id` | int | non* | ID d'une adresse sauvegardée |
| `adresse_livraison_text` | string | non* | Adresse en texte libre |
| `ville_livraison` | string | non | Ex : `"Port-au-Prince"` |
| `departement_livraison` | string | non | Ex : `"Ouest"` |
| `notes` | string | non | Notes pour le producteur |
| `preuve_paiement` | file | non** | Image JPG/PNG si `hors_ligne` |

> *`adresse_livraison_id` OU `adresse_livraison_text` — au moins un requis pour `domicile`
> **Optionnel lors de la création, peut être soumis séparément via `/api/payments/preuve/`

### Réponse — succès `201`

```json
{
  "success": true,
  "data": {
    "message": "1 commande(s) créée(s) avec succès !",
    "commandes": [
      {
        "numero_commande": "CMD-2026-00001",
        "producteur": "Jean Farmer",
        "total": "5000.00",
        "statut": "En attente de confirmation"
      }
    ],
    "redirect_url": "https://...",      // ← présent si moncash ou natcash
    "transaction_id": "TXN-XXXXXX"     // ← présent si moncash ou natcash
  }
}
```

### Comportement selon la méthode

| Méthode | Comportement |
|---|---|
| `moncash` | Commande créée + `redirect_url` retournée → ouvrir WebView Plopplop |
| `natcash` | Commande créée + `redirect_url` retournée → ouvrir WebView Plopplop |
| `cash` | Commande créée, paiement confirmé en espèces à la livraison |
| `hors_ligne` | Commande créée, preuve de virement à soumettre séparément |

---

## 2. Initier un paiement pour une commande existante

> Utile si la commande a déjà été créée et qu'on veut initier/ré-initier le paiement.

```
POST /api/payments/initier/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

| Champ | Type | Requis | Valeurs |
|---|---|---|---|
| `commande_numero` | string | oui | Ex : `"CMD-2026-00001"` |
| `type_paiement` | string | oui | `"cash"` \| `"moncash"` \| `"natcash"` \| `"virement"` |
| `numero_expediteur` | string | non | Numéro de téléphone MonCash/NatCash |
| `notes` | string | non | Note libre |

### Réponse — succès `201`

```json
{
  "success": true,
  "data": {
    "id": 12,
    "commande": "CMD-2026-00001",
    "type_paiement": "moncash",
    "statut": "initié",
    "montant": "5000.00",
    "redirect_url": "https://...",   // ← si moncash
    "moncash_token": "TOKEN_MC"      // ← si moncash
  }
}
```

---

## 3. Soumettre une preuve de paiement (cash / virement hors ligne)

```
POST /api/payments/preuve/
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

### Body (form-data)

| Champ | Type | Requis | Description |
|---|---|---|---|
| `paiement_id` | int | oui | ID du paiement obtenu à l'étape précédente |
| `preuve_image` | file | oui | Image JPG ou PNG (capture reçu / virement) |
| `id_transaction` | string | non | Référence de transaction |
| `montant_recu` | decimal | non | Montant reçu en HTG |

### Réponse — succès `200`

```json
{
  "success": true,
  "data": {
    "id": 12,
    "statut": "preuve soumise",
    "message": "Preuve de paiement reçue. L'admin va vérifier et confirmer votre commande."
  }
}
```

---

## 4. Vérifier le statut d'un paiement

```
POST /api/payments/verifier/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

```json
{ "paiement_id": 12 }
// OU
{ "id_transaction": "TXN-XXXXXX" }
```

### Réponse

```json
{
  "success": true,
  "data": {
    "id": 12,
    "statut": "confirmé",       // initié | en_attente | preuve soumise | vérifié | confirmé | échoué
    "type_paiement": "moncash",
    "montant": "5000.00",
    "moncash_data": { ... }     // ← présent si moncash + id_transaction fourni
  }
}
```

---

## 5. Vérifier un paiement MonCash / NatCash via Plopplop

> À appeler après retour de la WebView de paiement Plopplop.

```
POST /api/payments/plopplop-verify/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

```json
{ "commande_ref": "CMD-2026-00001" }
```

### Réponse — paiement confirmé

```json
{
  "success": true,
  "confirme": true,
  "montant": "5000.00",
  "method": "moncash",
  "transaction": "TXN-XXXXXX",
  "commandes": [{ "numero_commande": "CMD-2026-00001", "total": "5000.00" }]
}
```

### Réponse — paiement en attente

```json
{
  "success": true,
  "confirme": false,
  "statut": "no"
}
```

---

## 6. Historique des paiements de l'utilisateur

```
GET /api/payments/mes-paiements/
Authorization: Bearer <token>
```

### Réponse

```json
{
  "success": true,
  "data": [
    {
      "id": 12,
      "commande": "CMD-2026-00001",
      "type_paiement": "moncash",
      "statut": "confirmé",
      "montant": "5000.00",
      "created_at": "2026-04-09T10:00:00Z"
    }
  ]
}
```

---

## 7. Valider un code voucher (réduction)

```
POST /api/payments/voucher/valider/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

```json
{
  "code": "BIENVENUE10",
  "montant_commande": 5000.00
}
```

### Réponse

```json
{
  "success": true,
  "data": {
    "code": "BIENVENUE10",
    "remise": 500.00,
    "montant_final": 4500.00,
    "type_remise": "pourcentage"    // ou "fixe"
  }
}
```

---

## 8. Mes vouchers disponibles

```
GET /api/payments/voucher/mes-vouchers/
Authorization: Bearer <token>
```

---

## Flux complet Flutter — selon la méthode de paiement

### A. MonCash ou NatCash

```
1. POST /api/orders/commander/ { methode_paiement: "moncash", ... }
2. Récupérer response.data.redirect_url
3. Ouvrir WebView → redirect_url (passerelle Plopplop)
4. Détecter retour (URL de callback ou fermeture WebView)
5. POST /api/payments/plopplop-verify/ { commande_ref: "CMD-..." }
6. Si confirme == true → afficher confirmation
   Sinon → polling ou message "en attente"
```

### B. Cash (espèces à la livraison)

```
1. POST /api/orders/commander/ { methode_paiement: "cash", ... }
2. Afficher confirmation commande directement
   (pas d'étape paiement supplémentaire)
```

### C. Hors ligne / Virement bancaire

```
1. POST /api/orders/commander/ { methode_paiement: "hors_ligne", ... }
2. Récupérer le numero_commande
3. POST /api/payments/initier/ { commande_numero, type_paiement: "virement" }
4. Récupérer paiement_id
5. Utilisateur fait le virement et capture le reçu
6. POST /api/payments/preuve/ (multipart) { paiement_id, preuve_image }
7. Afficher "En attente de vérification admin"
```

---

## Codes d'erreur courants

| Code HTTP | Signification |
|---|---|
| `401` | Token manquant ou expiré → relancer login |
| `403` | Rôle insuffisant (pas acheteur) |
| `400` | Données invalides (voir champ `error`) |
| `503` | Passerelle de paiement (Plopplop/MonCash) indisponible |

---

## Statuts de paiement (enum)

| Valeur API | Description |
|---|---|
| `initié` | Paiement créé, rien encore reçu |
| `en_attente` | En attente d'action utilisateur |
| `preuve soumise` | Image de preuve reçue, attente vérif admin |
| `vérifié` | Plopplop / MonCash a confirmé |
| `confirmé` | Admin a validé — commande active |
| `échoué` | Paiement rejeté ou annulé |

---

## Statuts de commande (enum)

| Valeur | Description |
|---|---|
| `EN_ATTENTE` | Créée, pas encore confirmée |
| `CONFIRMEE` | Confirmée par le producteur |
| `EN_PREPARATION` | En cours de préparation |
| `PRETE` | Prête pour livraison / collecte |
| `EN_COLLECTE` | En route |
| `LIVREE` | Livrée à l'acheteur |
| `ANNULEE` | Annulée |
| `LITIGE` | En litige |
