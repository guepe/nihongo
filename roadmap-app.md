# Roadmap : application de révision maison

Objectif : remplacer Anki par notre propre application de révision, construite sur les
données de ce dépôt.

- **Appareils** : Mac, iPhone, navigateur web.
- **Utilisateurs** : plusieurs, chacun avec sa progression, derrière un login.
- **Synchro** : on révise sur un appareil, on reprend sur un autre.
- **Hébergement** : l'offre OVH Web Cloud déjà payée. Aucun coût en plus.
- **Historique Anki** : pas d'import, on repart de zéro.

---

## Choix techniques

### Une PWA plutôt qu'une app native

Une PWA est un site web qu'on peut « installer » : il a son icône sur l'écran d'accueil,
s'ouvre en plein écran et fonctionne hors-ligne. Une seule base de code sert tous les
appareils, sans App Store ni compte développeur Apple (99 €/an).

- iPhone : Safari → Partager → « Sur l'écran d'accueil ».
- Mac : Safari → Fichier → « Ajouter au Dock » (ou Chrome → « Installer »).

### Pile technique

| Brique | Choix | Pourquoi |
|---|---|---|
| Front | Vite + TypeScript + **Svelte** | Léger et simple ; produit des fichiers statiques |
| Algorithme de révision | **FSRS** (`ts-fsrs`) | Celui qu'utilise Anki aujourd'hui, open source |
| Stockage local | IndexedDB via Dexie | Les révisions marchent hors-ligne |
| API | **PHP 8.4**, sans framework (quelques fichiers) | Seul langage serveur fourni par OVH Web Cloud |
| Base de données | **MySQL** fournie par OVH | Comptes, sessions, journal des révisions |
| HTTPS | Let's Encrypt (gratuit chez OVH) | Obligatoire pour qu'une PWA s'installe |
| Déploiement | Script `deploy.sh` (build + `rsync` par SSH) | Une commande pour publier ; n'envoie que ce qui a changé |

L'app et l'API sont sur le même sous-domaine, **`hachi.guepe.com`** (蜂, *hachi* :
guêpe), avec l'API sous `hachi.guepe.com/api/`. Il n'y a donc pas de CORS à configurer.

### Architecture

```
dépôt nihongo                        OVH Web Cloud
─────────────                        ────────────────────────────────
vocabulary/*.toml                    /             app (fichiers statiques)
      │                              /deck.json    données du deck
      ▼                              /api/*.php    login, synchro
cardgen/export_json.py ──► deck.json       │
                                           ▼
                                     MySQL : users, sessions, review_events

iPhone / Mac / navigateur
─────────────────────────
PWA ─► IndexedDB (deck, révisions, file d'envoi) ◄──► /api
```

### Identifiants des cartes

Chaque carte a un identifiant **stable** de la forme `<note>:<type de carte>` :

- note de vocabulaire : `kanji + kana`, comme dans Anki ;
- note de conjugaison : `kanji + kana + groupe` ;
- type de carte : nom court (`fr-jp`, `furigana`, `kanji`, `kana`, `present-plain-neg-fr-jp`…).

Corriger une traduction, un tag ou un niveau ne change pas l'identifiant, donc la
progression est conservée. Corriger un kanji ou un kana crée une nouvelle carte, comme
dans Anki.

### Synchro par journal d'événements

On ne synchronise pas l'état des cartes : on synchronise **les révisions**.

1. Chaque réponse (« À revoir », « Difficile », « Bien », « Facile ») crée un événement :
   `{id (UUID), carte, note, date, appareil}`. Il est écrit dans IndexedDB puis placé
   dans une file d'envoi.
2. La file est envoyée à l'API dès qu'il y a du réseau. L'UUID évite les doublons si un
   envoi est répété.
3. Chaque appareil récupère les événements arrivés depuis sa dernière synchro.
4. L'état FSRS d'une carte (échéance, stabilité, difficulté) est **recalculé** en
   rejouant ses événements dans l'ordre chronologique.

On ne fait qu'ajouter des événements, donc deux appareils ne peuvent jamais se
contredire : pas de conflit à gérer. Annuler une réponse = ajouter un événement
`undo`.

### Volume de cartes

| Deck | Notes | Cartes possibles |
|---|---|---|
| Vocabulaire | ~3 200 | ~6 500 (2 à 3 par mot) |
| Conjugaison | 197 verbes | ~18 900 (96 par verbe) |

On ne peut pas tout ouvrir d'un coup. L'utilisateur choisit ce qu'il étudie : decks,
niveaux JLPT, et pour la conjugaison les formes à activer (par exemple d'abord présent
et passé, puis les autres). Les nouvelles cartes sont limitées par jour.

---

## Phase A : export des données

But : un fichier `deck.json` que l'app peut lire, généré depuis les TOML.

- [ ] `cardgen/export_json.py`, qui réutilise le code de `generate_*.py` : notes, types
      de cartes, kanji, kana, romaji, français, niveau, tags, fréquences ; formes
      conjuguées (kanji, kana, romaji, français) pour chaque verbe.
- [ ] Mêmes règles que les decks Anki : `config/kanji-only-vocab.txt` et
      `config/suspended.txt` respectés, verbes sans `french-conjugated` complet ignorés.
- [ ] Un numéro de version (hash du contenu) en tête du fichier, pour que l'app voie
      qu'il a changé.
- [ ] `generer.sh` produit aussi `deck.json`.

**Terminé quand** : `deck.json` contient toutes les notes des deux decks et pèse un poids
raisonnable (objectif : moins de 3 Mo compressé).

## Phase B : révision en local

But : réviser dans le navigateur, sans compte ni serveur. **L'app devient utile ici.**

- [ ] Projet `app/` (Vite + Svelte + TypeScript), lancé avec `npm run dev`.
- [ ] Chargement de `deck.json` dans IndexedDB.
- [ ] Écran d'accueil : cartes à réviser aujourd'hui, nouvelles cartes du jour, bouton
      « Commencer ».
- [ ] Écran de révision : recto → « Montrer la réponse » → 4 boutons avec le prochain
      intervalle affiché (« 10 min », « 3 j »…). Raccourcis clavier sur Mac
      (espace, 1 à 4).
- [ ] Mise en page des cartes reprise des decks Anki : kanji, kana en bleu, romaji en
      gris italique au verso, niveau et fréquence en bas.
- [ ] FSRS avec les paramètres par défaut ; rétention visée réglable (90 % par défaut).
- [ ] Réglages : decks et niveaux étudiés, formes de conjugaison activées, nouvelles
      cartes par jour (20 par défaut).
- [ ] Bouton « Annuler la dernière réponse ».

**Terminé quand** : on peut faire une vraie session de révision sur Mac, fermer le
navigateur, revenir le lendemain et retrouver les bonnes cartes à réviser.

## Phase C : PWA

But : installer l'app sur l'iPhone et le Mac, et réviser hors-ligne.

- [ ] Manifest (nom, icônes, couleurs) et service worker (`vite-plugin-pwa`).
- [ ] Toute l'app et `deck.json` en cache : elle s'ouvre en mode avion.
- [ ] Mise en page mobile : gros boutons en bas de l'écran, à portée de pouce ; mode
      sombre.
- [ ] Mise en ligne provisoire sur `hachi.guepe.com` pour tester sur l'iPhone.

**Terminé quand** : l'app installée sur l'iPhone fonctionne en mode avion.

> ⚠️ Sans synchro, chaque appareil a sa propre progression pendant cette phase.

## Phase D : comptes et synchro

But : plusieurs utilisateurs, et la même progression sur tous les appareils.

### Base MySQL

| Table | Contenu |
|---|---|
| `users` | id, nom, e-mail, `password_hash`, date de création |
| `invitations` | code, créé par, utilisé par, date d'expiration |
| `sessions` | hash du jeton, utilisateur, appareil, dernière utilisation |
| `review_events` | n° de séquence, UUID, utilisateur, carte, note, date, appareil |
| `settings` | utilisateur, réglages (JSON) |

### API PHP

| Route | Rôle |
|---|---|
| `POST /api/register` | Création de compte **avec un code d'invitation** |
| `POST /api/login` / `POST /api/logout` | Ouvre ou ferme une session ; renvoie un jeton |
| `POST /api/events` | Envoie un lot d'événements (doublons ignorés grâce à l'UUID) |
| `GET /api/events?since=N` | Événements de l'utilisateur après le n° de séquence N |
| `GET` / `PUT /api/settings` | Réglages de l'utilisateur |
| `POST /api/invitations` | Crée un code d'invitation (admin) |

- [ ] Mots de passe : `password_hash` / `password_verify`. Jetons aléatoires, stockés
      hachés en base, envoyés dans l'en-tête `Authorization`.
- [ ] Requêtes préparées (PDO) partout ; limite de tentatives de login.
- [ ] Fichier `config.php` (identifiants MySQL) hors du dépôt git.
- [ ] Écrans login / inscription dans l'app ; la session reste ouverte sur l'appareil.
- [ ] Synchro au démarrage, après chaque réponse (si réseau), et au retour en ligne.
      Indicateur discret : « synchronisé », « 3 révisions en attente ».
- [ ] La première connexion sur un appareil déjà utilisé hors-ligne envoie ses révisions
      locales au compte.

**Terminé quand** : deux utilisateurs ont chacun leur progression, et une révision faite
sur l'iPhone apparaît sur le Mac.

## Phase E : déploiement

- [ ] Sous-domaine `hachi.guepe.com` créé chez OVH, HTTPS Let's Encrypt activé, PHP 8.4 sélectionné.
- [ ] Base MySQL créée ; script `api/schema.sql` pour les tables.
- [ ] `deploy.sh` : build de l'app, export de `deck.json`, envoi par `rsync` sur SSH.
- [ ] Clé SSH dédiée au déploiement ; `config.php` créé une fois à la main sur le serveur.
- [ ] `.htaccess` : routes `/api/*`, en-têtes de cache (le service worker ne doit jamais
      être mis en cache par le navigateur).
- [ ] Sauvegarde : export régulier de `review_events` (c'est toute la progression).

## Phase F : confort

- [ ] Statistiques : révisions par jour, série de jours, rétention, prévisions des
      prochains jours.
- [ ] Audio : lecture du mot avec la synthèse vocale japonaise du navigateur.
- [ ] Furigana au-dessus des kanji (option).
- [ ] Mise à jour du deck : nouveaux mots ajoutés comme nouvelles cartes, mots retirés
      masqués (leur historique est gardé).
- [ ] Recherche dans le vocabulaire, suspension manuelle d'une carte.
- [ ] Optimisation des paramètres FSRS sur l'historique de chacun (après quelques
      milliers de révisions).

---

## Décisions

- Sous-domaine : `hachi.guepe.com`.
- Hébergement : OVH Web Cloud, PHP 8.4, accès SSH et FTP.
- Le dépôt reste **la seule source** des cartes : on ne modifie pas une carte depuis l'app.
  Pour corriger une carte, on édite le TOML, on régénère `deck.json` et on redéploie.
