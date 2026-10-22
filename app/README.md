# hachi (蜂)

Application de révision des decks de ce dépôt (voir [roadmap-app.md](../roadmap-app.md)).

## Lancer en local

```sh
./generer.sh          # à la racine du dépôt : produit app/public/deck.json
cd app
npm install           # la première fois (voir la note ci-dessous)
npm run dev           # puis ouvrir http://localhost:5173
```

- `npm test` : tests de la planification (FSRS, rejeu des révisions, annulation…).
- `npm run check` : vérification des types.
- `npm run build` : version de production dans `dist/`.

> npm 10.8 plante à l'installation (`Cannot read properties of null (reading 'edgesOut')`).
> Utiliser npm 11 : `npx npm@11 install`.

## Mise en ligne

```sh
cp deploy.env.example deploy.env   # une seule fois, puis compléter
./deploy.sh                        # à la racine du dépôt
```

Le script régénère `deck.json`, lance les tests, construit l'app et l'envoie par `rsync`
sur SSH. Il refuse d'envoyer dans un dossier qui contient autre chose que l'app.

## Organisation

| Fichier | Rôle |
|---|---|
| `src/lib/types.ts` | Format de `deck.json` |
| `src/lib/cards.ts` | Liste des cartes et ordre des nouvelles cartes |
| `src/lib/scheduler.ts` | Planification FSRS, recalculée à partir du journal des révisions |
| `src/lib/settings.ts` | Réglages et valeurs par défaut |
| `src/lib/db.ts` | Stockage local (IndexedDB) : révisions, réglages, identifiant de l'appareil |
| `src/components/` | Écrans : accueil, révision, réglages ; bannière de mise à jour |
| `public/.htaccess` | Configuration Apache d'OVH : HTTPS, cache, compression |

La progression d'une carte n'est jamais enregistrée : seules les réponses le sont, et
l'état de chaque carte est recalculé en les rejouant. C'est ce qui permettra de fusionner
les révisions de plusieurs appareils (phase D).
