日本語
======
Notes et outils pour apprendre le japonais, avec des decks Anki **français → japonais**.

Ce dépôt est un fork de [echelon/nihongo](https://github.com/echelon/nihongo), dont le
vocabulaire et les scripts ont été adaptés en français. Les gloses anglaises d'origine
sont conservées (champ `english`) comme référence et pour faciliter la reprise des
nouveautés du projet d'origine. L'avancement de l'adaptation est suivi dans
[roadmap.md](roadmap.md).

Démarrage rapide (débutants)
----------------------------
Pas besoin de Python ni de ligne de commande : il suffit d'installer Anki et d'importer
deux fichiers.

### 1. Installer Anki

Anki est un logiciel de cartes de révision (flashcards) qui vous fait réviser chaque mot
juste avant que vous l'oubliiez.

| Appareil | Application | Prix | Lien |
|---|---|---|---|
| Windows 10 / 11 | Anki | gratuit | [apps.ankiweb.net](https://apps.ankiweb.net/) |
| Mac (macOS 13 ou plus récent) | Anki | gratuit | [apps.ankiweb.net](https://apps.ankiweb.net/) |
| Linux | Anki | gratuit | [apps.ankiweb.net](https://apps.ankiweb.net/) |
| iPhone / iPad | AnkiMobile | payant | [App Store](https://apps.apple.com/app/ankimobile-flashcards/id373493387) |
| Android | AnkiDroid | gratuit | [Google Play](https://play.google.com/store/apps/details?id=com.ichi2.anki) |

- **Windows** : sur [apps.ankiweb.net](https://apps.ankiweb.net/), cliquez sur **Windows**
  (*x64* pour la plupart des PC, *ARM* seulement pour les PC à processeur ARM). Lancez le
  fichier téléchargé et suivez l'installation en gardant les options par défaut.
- **Mac** : sur [apps.ankiweb.net](https://apps.ankiweb.net/), choisissez **Apple Silicon**
  si votre Mac a une puce Apple (M1, M2…), sinon **Intel**. Pour le savoir : menu Pomme () →
  **À propos de ce Mac**. Ouvrez le fichier `.dmg` téléchargé et glissez Anki dans le dossier
  **Applications**. Au premier lancement, si macOS bloque l'ouverture, faites un clic droit
  sur Anki → **Ouvrir**.
- **Téléphone** : installez l'application depuis l'App Store ou Google Play.

Au premier lancement, Anki demande la langue de l'interface : choisissez **Français**.
Le [guide officiel](https://docs.ankiweb.net/) (en anglais) détaille l'installation.

### 2. Télécharger les decks

| Deck | Contenu | Téléchargement |
|---|---|---|
| Japonais généré | ~3 200 mots de vocabulaire (JLPT n5 à n1) | [japonais_fr.apkg](https://github.com/guepe/nihongo/releases/latest/download/japonais_fr.apkg) |
| Japonais généré - conjugaison | ~200 verbes, 13 formes de conjugaison | [japonais_conjugaison_fr.apkg](https://github.com/guepe/nihongo/releases/latest/download/japonais_conjugaison_fr.apkg) |

Toutes les versions sont sur la page [Releases](https://github.com/guepe/nihongo/releases).

### 3. Importer les decks

- **Sur ordinateur** : double-cliquez sur le fichier `.apkg` téléchargé, ou dans Anki :
  **Fichier → Importer…** puis choisissez le fichier. Faites-le pour les deux fichiers.
- **Sur téléphone**, deux possibilités :
  - **Le plus simple** : importez d'abord les decks sur ordinateur, créez un compte gratuit
    sur [AnkiWeb](https://ankiweb.net/), cliquez sur **Synchroniser** dans Anki, puis
    connectez-vous avec le même compte dans l'application mobile et synchronisez. Vos
    révisions restent ensuite synchronisées entre tous vos appareils.
  - **Sans ordinateur** : téléchargez le fichier `.apkg` sur le téléphone, ouvrez-le et
    choisissez AnkiDroid ou AnkiMobile pour l'importer.

C'est tout : cliquez sur un deck puis sur **Étudier**. Comptez 10 à 20 nouvelles cartes
par jour pour commencer.

### Mettre à jour les decks

Quand une nouvelle version est publiée, téléchargez à nouveau les fichiers et importez-les
de la même façon. **Votre progression est conservée.** Si Anki propose une option pour
les notes existantes, choisissez de les **mettre à jour**.

### Générer les decks soi-même

Pour générer les fichiers à partir du vocabulaire du dépôt (par exemple après l'avoir
modifié), il faut [Python 3](https://www.python.org/downloads/). Ensuite, un seul script
fait tout, y compris l'installation au premier lancement :

- **Mac / Linux** : dans un terminal, depuis le dossier du dépôt, lancez `./generer.sh`.
- **Windows** : double-cliquez sur `generer.bat`.

Les fichiers `.apkg` sont créés dans le dossier du dépôt. Pour le détail, voir
[Générer les fichiers `.apkg`](#générer-les-fichiers-apkg).

Organisation des fichiers
-------------------------
- `vocabulary/` : fichiers TOML contenant le vocabulaire annoté, rangé par thème ou par
  liste JLPT. Chaque mot a une traduction française (`french`), affichée sur les cartes.

  Dans la mesure du possible, chaque mot n'a qu'un ou deux sens, pour qu'il soit plus
  facile de mémoriser les synonymes et de les distinguer.

  **Important :** modifier la traduction d'un mot ne change pas l'identifiant de sa carte :
  l'historique de révision est conservé. Il en va de même quand on déplace un mot d'un
  fichier à l'autre ou qu'on change ses tags.

- `cardgen/` : scripts pour trier et normaliser le vocabulaire, suivre la traduction et
  générer les decks Anki. Lancez `sort.py` avant chaque commit qui touche aux fichiers
  TOML : il les garde propres et homogènes.

- `config/kanji-only-vocab.txt` : liste des mots (un par ligne) pour lesquels on ne veut
  pas d'aide en furigana. Le générateur crée alors une carte en kanji seul pour chaque mot
  dont le champ `kanji` figure dans cette liste. Videz ou adaptez ce fichier selon vos
  préférences.

- `config/suspended.txt` : liste des mots dont les cartes sont importées suspendues.

- `lists/` : listes de fréquence et listes JLPT utilisées par les scripts. Seule la
  partie japonaise sert ; elles ne sont pas à traduire.

- `book/` : notes de cours (pronoms, verbes, adjectifs, conjonctions, météo).

Installation
------------
Les scripts sont écrits en Python 3. Les dépendances s'installent dans un environnement
virtuel (`venv`) placé dans le dossier `python/`, qui est ignoré par git :

```bash
python3 -m venv python
source python/bin/activate
pip install -r requirements.txt
```

Cette installation ne se fait qu'une fois.

Générer les fichiers `.apkg`
----------------------------
Les fichiers `.apkg` sont les paquets qu'on importe dans Anki. Ils ne sont **pas** dans le
dépôt (ils sont ignorés par git) : il faut les générer soi-même, la première fois puis
après chaque modification du vocabulaire.

### En bref

Depuis la racine du dépôt :

```bash
source python/bin/activate
python cardgen/generate_vocabulary_deck.py
python cardgen/generate_verb_deck.py
```

Puis, dans Anki, **Fichier → Importer…** pour chacun des deux fichiers créés.

Les scripts `generer.sh` (Mac / Linux) et `generer.bat` (Windows) font la même chose et
installent l'environnement Python au premier lancement.

### Étape par étape

1. **Ouvrir un terminal à la racine du dépôt**, c'est-à-dire dans le dossier qui contient
   ce `README.md` :

   ```bash
   cd chemin/vers/nihongo
   ```

   C'est indispensable : les scripts lisent `config/`, `lists/` et `vocabulary/` avec des
   chemins relatifs.

2. **Activer l'environnement virtuel** (créé lors de l'installation, voir ci-dessus) :

   ```bash
   source python/bin/activate
   ```

   L'invite du terminal affiche alors `(python)`. À refaire dans chaque nouveau terminal.

3. **Facultatif, mais conseillé si vous avez modifié des fichiers TOML** : les normaliser.

   ```bash
   python cardgen/sort.py
   ```

4. **Générer le deck de vocabulaire** :

   ```bash
   python cardgen/generate_vocabulary_deck.py
   ```

   Le script liste les fichiers lus, puis affiche un résumé qui se termine ainsi :

   ```
   Total cards: 6394
   Total notes: 3197
     > notes disabled (deprecated): 8
     > notes suspended: 6
     > notes /w kanji-only cards: 464
     > notes w/ hiragana-only cards: 0
     > notes translated to French: 3197 / 3197
   Output file: japonais_fr.apkg
   ```

5. **Générer le deck de conjugaison** :

   ```bash
   python cardgen/generate_verb_deck.py
   ```

   Le script liste les fichiers de `vocabulary/verbs/` qu'il lit et crée
   `japonais_conjugaison_fr.apkg`. Une ligne `Skipping … incomplete french-conjugated`
   signale un verbe ignoré parce que ses formes françaises sont incomplètes (voir
   [Format des fichiers TOML](#format-des-fichiers-toml)).

6. **Importer dans Anki** : **Fichier → Importer…**, choisir `japonais_fr.apkg`, valider,
   puis recommencer avec `japonais_conjugaison_fr.apkg`. Si Anki propose une option pour
   les notes existantes, choisissez de les **mettre à jour**, sinon vos corrections de
   traduction ne seront pas prises en compte.

### Fichiers produits

Les deux fichiers sont créés à la racine du dépôt et remplacés à chaque génération.

| Fichier | Script | Deck dans Anki | Contenu |
|---|---|---|---|
| `japonais_fr.apkg` | `generate_vocabulary_deck.py` | Japonais généré | ~3 200 mots, 2 à 3 cartes par mot (français → japonais, kanji + kana → français, kanji seul…) |
| `japonais_conjugaison_fr.apkg` | `generate_verb_deck.py` | Japonais généré - conjugaison | ~200 verbes, 96 cartes par verbe (13 formes, affirmatif et négatif, neutre et poli, dans les deux sens) |

### Après une modification du vocabulaire

Refaites les étapes 2 à 6. Réimporter un deck **conserve votre progression** dans Anki,
tant que le `kanji` et le `kana` des mots ne changent pas (voir
[Régénérer sans perdre sa progression](#régénérer-sans-perdre-sa-progression)).

### En cas de problème

| Message | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'genanki'` | L'environnement virtuel n'est pas activé, ou les dépendances ne sont pas installées. | `source python/bin/activate`, et si besoin `pip install -r requirements.txt`. |
| `FileNotFoundError: … 'config/kanji-only-vocab.txt'` | Le script n'est pas lancé depuis la racine du dépôt. | `cd` vers le dossier qui contient ce `README.md`, puis relancer avec `python cardgen/…`. |
| `Skipping … incomplete french-conjugated` | Un verbe n'a pas toutes ses formes françaises. | Compléter son champ `french-conjugated`. Les autres verbes sont générés normalement. |
| Une erreur `toml` (`TomlDecodeError`…) | Un fichier TOML a été mal édité (guillemet, crochet…). | Le message indique la ligne ; corriger le fichier, puis lancer `python cardgen/sort.py`. |

Utilisation
-----------
### Principe

Le vocabulaire est rédigé à la main dans des fichiers TOML, puis les scripts de `cardgen/`
le transforment en paquets Anki (`.apkg`) à importer :

```
vocabulary/**/*.toml  +  config/*.txt  ──►  cardgen/generate_*.py  ──►  .apkg  ──►  Anki
```

Il est très utile de connaître la différence entre une *note* et une *carte* dans Anki
(voir le manuel d'Anki). Chaque entrée `[[cards]]` d'un fichier TOML devient une **note**,
et chaque note produit plusieurs **cartes** : français → japonais, kanji + kana → français, etc.

Pour produire les decks, voir [Générer les fichiers `.apkg`](#générer-les-fichiers-apkg).
Comme pour ces scripts, **lancez toujours les autres scripts depuis la racine du dépôt**.

Le deck de conjugaison propose, pour chaque verbe, 13 formes (présent, passé, volitif,
impératif, conditionnels, potentiel, causatif, passif…), à la forme affirmative et
négative, en registre neutre et poli, dans les deux sens (FR → JP et JP → FR).

### Régénérer sans perdre sa progression

Les noms et identifiants des decks et des modèles sont fixes. L'identifiant de chaque note
est calculé à partir de ses champs `kanji` et `kana` uniquement. Vous pouvez donc modifier
le vocabulaire (ajouter, corriger ou retirer des mots, changer les réglages kanji seul),
puis régénérer et réimporter le deck, sans perdre l'historique de révision.

- Modifier n'importe quel champ **autre** que `kanji` et `kana` (traduction, tags,
  niveau…) conserve la progression.
- Modifier le `kanji` ou le `kana` crée une **nouvelle** note : l'historique de l'ancienne
  est perdu.

> ⚠️ Ne changez pas les identifiants, les noms ni l'ordre des champs et des cartes dans
> le code des générateurs sans être d'abord passé par l'interface d'Anki : vous perdriez
> votre progression ou vous créeriez un modèle en double.

### Configuration

- `config/kanji-only-vocab.txt` : un mot par ligne (valeur du champ `kanji`). Ces mots
  n'auront pas de carte avec furigana, seulement une carte en kanji seul.
- `config/suspended.txt` : un mot par ligne. Ses cartes sont importées **suspendues** et
  reçoivent les tags `suspended` et `suspended_by_config`.

Changer le réglage kanji seul / furigana d'un mot change les cartes générées pour ce mot :
les templates rendent « vides » les cartes non voulues, et Anki ne crée pas de carte vide.
En revanche, Anki ne supprime pas tout seul une carte déjà étudiée qui devient vide. Pour
la retirer (avec son historique), utilisez **Outils → Vérifier les cartes vides**
(*Empty Cards*).

### Scripts utilitaires

| Commande | Rôle |
|---|---|
| `python cardgen/sort.py` | Trie et normalise les fichiers TOML et `config/*.txt`. **À lancer avant chaque commit.** |
| `python cardgen/update_frequencies.py` | Ajoute dans les TOML les scores de fréquence tirés de `lists/` (anime, Leeds, Wikipédia, romans). |
| `python cardgen/frequency.py --jlpt n5 n4` | Liste les mots JLPT absents du vocabulaire. Aussi `--anime`, `--wanikani` et `--limit N`. |
| `python cardgen/insert_blank_notes.py` | Ajoute une entrée vide (avec `french`, et `french-conjugated` pour les verbes) en tête de chaque fichier pour saisir des mots à la main ; `sort.py` retire celles qui restent vides. |
| `python cardgen/tsv_import.py` | Ajoute aux fichiers `vocabulary/generated_*.toml` les mots des `lists/*.tsv` qui manquent encore. Colonnes : kanji, kana, anglais, niveau et, en option, français. |
| `python cardgen/translation_status.py` | Suivi de la traduction (voir ci-dessous). |
| `python cardgen/generate_verb_deck.py --test` | Lance les tests unitaires du conjugueur. |

### Traduire en français

Le script `cardgen/translation_status.py` sert à suivre et à faire la traduction, par
exemple après avoir récupéré de nouveaux mots du projet d'origine :

```bash
python cardgen/translation_status.py                         # avancement par fichier et par niveau JLPT
python cardgen/translation_status.py --missing --level n5    # mots n5 pas encore traduits
python cardgen/translation_status.py --export n5.tsv --level n5 --limit 200
#   … remplir la colonne « french » (tableur, LLM…), sans toucher aux autres colonnes …
python cardgen/translation_status.py --import n5.tsv         # réécrit `french` dans les TOML
python cardgen/generate_vocabulary_deck.py                   # puis réimporter dans Anki
```

Le TSV contient les colonnes `kanji`, `kana`, `level`, `english`, `french` et `file`.
L'import retrouve chaque mot grâce au trio `kanji` + `kana` + `english`, puis place `french`
juste après `english`. Un mot présent dans plusieurs fichiers est mis à jour partout.
`--export --all` inclut aussi les mots déjà traduits, pour les relire.

Un mot sans traduction reste utilisable : sa carte affiche l'anglais et reçoit le tag
`a_traduire`.

#### Conventions de traduction

| Cas | Exemple |
|---|---|
| Un ou deux sens, séparés par `; ` | 高い → `haut; cher` |
| Nom sans article | 段落 → `paragraphe` |
| Adjectif au masculin singulier | 新しい → `nouveau` |
| Verbe à l'infinitif ; garder le `~` des verbes transitifs | 開ける → `ouvrir ~` |
| Précisions traduites entre parenthèses | `(soutenu)`, `(familier)`, `(litt. « … »)` |
| Mot d'emprunt : le mot français de la chose | ワイシャツ → `chemise de costume` |
| Si l'anglais est faux, suivre le japonais | 匂い → `odeur; parfum` |

Format des fichiers TOML
------------------------

### Vocabulaire (sauf verbes)

```toml
[[cards]]
kanji = '' # Kanji. Pour un mot d'emprunt, le katakana (répété dans kana pour l'instant).
kana = '' # Hiragana ou katakana, qui sert de furigana.
english = '' # Glose anglaise d'origine (référence). Plusieurs sens séparés par ';'.
french = '' # Traduction française, affichée sur les cartes. Sans elle, l'anglais est affiché et la note reçoit le tag 'a_traduire'.
source = '' # Provenance du mot.
level = 'n[1-5]' # Niveau JLPT : n1, n2, n3, n4, n5. Absent si le mot n'est pas au JLPT.
explain = '' # Lien facultatif pour en savoir plus.
tags = [] # Tags libres. 'common' signale un mot fréquent.
```

### Verbes

```toml
[[cards]]
kanji = '' # Kanji. Pour un mot d'emprunt, le katakana (répété dans kana pour l'instant).
kana = '' # Hiragana ou katakana, qui sert de furigana.
english = '' # Glose anglaise d'origine. Un '~' signale un verbe transitif.
french = '' # Traduction française (infinitif). Garder le '~' si transitif.
english-conjugated = { base = '', past = '', plural = '', continuous = '' } # Formes anglaises d'origine.
french-conjugated = { infinitif = '', present = '', participe = '', auxiliaire = 'avoir', imperatif = '', nous = '' } # Formes de base pour le deck de conjugaison (voir ci-dessous).
verb-type = '' # ichidan, godan-mu, godan-bu, etc.
transitive = false # Verbe transitif ou non.
level = 'n[1-5]' # Niveau JLPT : n1, n2, n3, n4, n5. Absent si le mot n'est pas au JLPT.
explain = '' # Lien facultatif pour en savoir plus.
tags = [] # Tags libres. 'common' signale un mot fréquent.
```

Dans `french-conjugated`, chaque valeur est une forme nue du verbe français (sans
pronom, sans « se », sans complément) :

| Clé | Contenu | Exemple (s'approcher) |
|---|---|---|
| `infinitif` | infinitif | `approcher` |
| `present` | présent, 3ᵉ personne du singulier | `approche` |
| `participe` | participe passé, masculin singulier | `approché` |
| `auxiliaire` | `avoir` ou `être` (les verbes pronominaux prennent `être` automatiquement) | `avoir` |
| `imperatif` | impératif, 2ᵉ personne du singulier | `approche` |
| `nous` | impératif, 1ʳᵉ personne du pluriel (« approchons ! ») | `approchons` |
| `pronominal` | `true` pour un verbe pronominal (facultatif) | `true` |
| `complement` | mots placés après le verbe (facultatif) : `ensemble`, `du doigt` | |

`generate_verb_deck.py` en tire les 13 formes françaises du deck (« s'est approché »,
« ne t'approche pas ! », « va sans doute s'approcher »…), avec la négation et l'élision.
Un verbe dont `french-conjugated` est incomplet est ignoré, avec un avertissement.

Recherches utiles dans Anki
---------------------------
Toutes les _cartes_ sans niveau JLPT :

```
"note:Modèle japonais (FR)" -level:n1 -level:n2 -level:n3 -level:n4 -level:n5 card:1
```

Les notes pas encore traduites en français :

```
tag:a_traduire
```

Apprendre les kanji
-------------------
- 2 136 kanji jōyō (école primaire et collège)
  - 1 006 enseignés à l'école primaire (les kyōiku kanji)
  - 1 130 enseignés dans le secondaire
  - 862 kanji supplémentaires autorisés pour les prénoms (hors jōyō)

- WaniKani est un site de révision espacée (SRS) utile, qui enseigne :
  - 2 027 kanji
  - 6 287 mots de vocabulaire

JLPT
----

Niveaux :

- n5 : débutant. 800 mots, 100 kanji, environ 150 heures d'étude.
  « Comprendre un peu de japonais de base. »
- n4 : élémentaire. 1 500 mots, 300 kanji, 300 heures.
  « Comprendre le japonais de base. »
- n3 : intermédiaire. 3 700 mots, 650 kanji, 450 heures.
  « Comprendre dans une certaine mesure le japonais de la vie quotidienne. »
- n2 : pré-avancé. 6 000 mots, 1 000 kanji, 600 heures.
  « Comprendre le japonais de la vie quotidienne, et dans une certaine mesure celui
  de situations variées. »
- n1 : avancé. 10 000 à 18 000 mots, 2 000 kanji, 900 heures.
  « Comprendre le japonais utilisé dans des situations variées. »

### Liens JLPT

- [Listes de vocabulaire du JLPT](https://jlptstudy.net/N5/) (en anglais)
- [Liste complète du vocabulaire du JLPT N5](https://nihongoichiban.com/2011/04/30/complete-list-of-vocabulary-for-the-jlpt-n5/) (en anglais)
- [À propos du JLPT](http://www.tanos.co.uk/jlpt/aboutjlpt/) (en anglais)
- [こいつ, そいつ, あいつ, どいつ](https://www.japanesewithanime.com/2016/10/koitsu-soitsu-aitsu-doitsu-meaning.html) (en anglais)

Autres liens
------------

- [jisho.org : dictionnaire japonais](https://jisho.org/) (japonais-anglais)
- [Irasshai (cours vidéo de japonais I et II)](http://www.gpb.org/irasshai) (en anglais)
- [Sous-titres d'anime en japonais](http://kitsunekko.net/)

Licence
-------
Domaine public, comme le projet d'origine.
