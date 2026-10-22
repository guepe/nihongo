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

## Phase A : export des données ✅

But : un fichier `deck.json` que l'app peut lire, généré depuis les TOML.

- [x] `cardgen/export_json.py` réutilise les notes des générateurs Anki
      (`generate_vocabulary_deck.load_notes()`, `generate_verb_deck.VERB_HASH`) : mêmes
      règles `config/*.txt`, mêmes traductions, mêmes romaji. Contrôlé : les 28 368
      champs de conjugaison sont identiques à ceux du deck Anki.
- [x] Identifiant de note = le GUID Anki (hash de kanji + kana, ou de kanji + kana +
      groupe pour les verbes). Une carte = (note, type de carte).
- [x] `version` = hash du contenu : elle ne change que si les cartes changent.
- [x] `generer.sh` et `generer.bat` produisent aussi `app/public/deck.json` (ignoré par git).
- [x] Résultat : 3 174 notes de vocabulaire (6 348 cartes) et 197 verbes (18 912 cartes) ;
      2,2 Mo, **306 Ko compressé**.
- [x] Corrigé au passage : niveau `n4study` → `n4` (理由) ; fichiers TOML lus dans
      l'ordre alphabétique, pour que deux générations donnent le même résultat.
- [x] **23 mots en double** (même kanji + kana dans deux fichiers : 船 trois fois, 方, 理由,
      明るい…) fusionnés dans les TOML : la première entrée est gardée, avec les tags et
      sources des autres et la traduction la plus complète. Pour 張る, 終わる et 曲がる,
      les formes conjuguées du deck de conjugaison sont conservées. `export_json.py`
      signale tout nouveau doublon.

Format de `deck.json` :

```jsonc
{
  "format": 1,                 // structure du fichier
  "version": "618c21c9ac69",   // hash du contenu
  "decks": {
    "vocabulary": {
      "name": "Japonais généré",
      "card_types": [{"id": "fr-jp", "label": "Français → Japonais"}, …],
      "notes": [{
        "id": "IyV$E?.Kg&", "kanji": "嘴", "kana": "くちばし", "romaji": "kuchibashi",
        "french": "bec", "level": "n1", "tags": ["birds", "common", "noun"],
        "frequency": {"score": 26989, "source": "anime"}, "suspended": false,
        "cards": ["fr-jp", "furigana"]
      }, …]
    },
    "conjugation": {
      "name": "Japonais généré - conjugaison",
      "directions": ["fr-jp", "jp-fr"],
      "conjugations": [{"id": "present_indicative", "label": "Présent", "hint": null,
                        "forms": ["plain.positive", "plain.negative", …]}, …],
      "notes": [{
        "id": "@4@ydyZ&j", "kanji": "会う", "kana": "あう", "romaji": "au",
        "french": "rencontrer; voir (quelqu'un)", "group": "godan-u", "level": "n5",
        "forms": {
          "present_indicative.plain.negative":
            {"kanji": "会わない", "kana": "あわない", "romaji": "awanai", "french": "ne rencontre pas"},
          …
        }
      }, …]
    }
  }
}
```

Chaque forme d'un verbe donne deux cartes, une par direction :
`present_indicative.plain.negative.fr-jp` et `….jp-fr`.

## Phase B : révision en local ✅

But : réviser dans le navigateur, sans compte ni serveur. **L'app devient utile ici.**

- [x] Projet `app/` (Vite 8 + Svelte 5 + TypeScript), lancé avec `npm run dev` (voir
      `app/README.md`).
- [x] `deck.json` chargé au démarrage ; les révisions et réglages sont dans IndexedDB
      (Dexie). L'état FSRS de chaque carte est recalculé en rejouant ses révisions.
- [x] Écran d'accueil : nouvelles cartes, cartes en cours et à réviser, par deck.
- [x] Écran de révision : recto → « Montrer la réponse » (ou toucher la carte) → 4 boutons
      avec le prochain intervalle (« 10 min », « 7 j »…). Raccourcis : espace / Entrée,
      1 à 4, ⌘Z pour annuler.
- [x] Cartes reprises des decks Anki : kanji, kana en bleu, romaji en gris italique,
      niveau et fréquence ; pour la conjugaison, tableau forme / verbe / sens / groupe.
- [x] FSRS (`ts-fsrs` 5) avec le « fuzz » activé : il est calculé à partir de la date et
      de l'état de la carte, donc identique sur tous les appareils.
- [x] Ordre : cartes en apprentissage échues, révisions, nouvelles cartes (en alternant
      les decks), puis apprentissage en avance de 20 min. Journée qui commence à 4 h,
      comme dans Anki.
- [x] Nouvelles cartes : vocabulaire du N5 au N1 puis sans niveau, du mot le plus
      fréquent au moins fréquent ; conjugaison verbe par verbe, des plus faciles aux
      plus difficiles.
- [x] Réglages : decks, nouvelles cartes par jour (15 vocabulaire, 5 conjugaison),
      niveaux JLPT, formes de conjugaison (présent et passé au départ), rétention visée
      (90 %).
- [x] Bouton « Annuler la dernière réponse », qui fonctionne aussi après un rechargement.
- [x] Cartes sœurs repoussées au lendemain, comme dans Anki : un seul sens par mot et par
      jour (FR → JP aujourd'hui, JP → FR demain), et par forme pour la conjugaison.
- [x] Mode sombre ; mise en page testée en largeur iPhone et Mac.
- [x] Tests (`npm test`) : liste des cartes, journée à 4 h, limites quotidiennes, carte
      ratée qui revient, rejeu dans le désordre identique, annulation, filtres.

**Terminé quand** : on peut faire une vraie session de révision sur Mac, fermer le
navigateur, revenir le lendemain et retrouver les bonnes cartes à réviser.

## Phase C : PWA

But : installer l'app sur l'iPhone et le Mac, et réviser hors-ligne.

- [x] Manifest (nom, icônes 蜂, couleurs) et service worker (`vite-plugin-pwa` 2).
- [x] Toute l'app et `deck.json` en cache : elle s'ouvre et enregistre les révisions en
      mode avion (testé dans Chromium : réseau coupé, révision, rechargement).
- [x] Mise à jour : bannière « Nouvelle version disponible » (on ne recharge jamais en
      pleine révision sans accord) ; vérification toutes les heures.
- [x] Mise en page mobile : gros boutons en bas de l'écran, zones sûres de l'iPhone ;
      mode sombre ; métadonnées iOS (icône, nom, plein écran).
- [x] `navigator.storage.persist()` : demande au navigateur de ne pas effacer la
      progression.
- [x] `deploy.sh` (+ `deploy.env`, non versionné) et `.htaccess` (HTTPS forcé, cache,
      compression). Garde-fou : refuse d'envoyer dans un dossier qui contient autre chose
      que l'app.
- [x] Mise en ligne sur `hachi.guepe.com` (utilisateur SSH dédié : son dossier personnel
      est la racine du site ; `rsync` ne supprime jamais les fichiers cachés comme `.ssh`).
      Vérifié en ligne : redirection HTTPS, compression (`deck.json` : 305 Ko), cache,
      fonctionnement hors-ligne.
- [ ] Test sur l'iPhone (Safari → Partager → « Sur l'écran d'accueil ») et le Mac.

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
