日本語
======
My personal notes and tools for learning the Japanese language.

I'm also teaching my friends, so some of this will be structured to aid learning.

File Layout
-----------
- `/vocabulary` - toml files with a wide variety of annotated vocabulary. These
  will be updated frequently during study.

  Where possible, there will only be one English meaning provided for each
  Japanese word. This is to aid in memorizing and recalling synonyms.

  **Important Note:** From time to time I may change the English definitions of
  words. This will not change the card's UUID / hash, so SRS data will be retained.
  I'll also be moving vocabulary around and adjusting the tagging, but that should
  be entirely non-destructive.

- `/cardgen` - utilities for sorting and normalizing the vocabulary as well as
  tools to turn the vocabulary into Anki decks. The `sort.py` normalization utility
  should be run before any changes to vocab toml files are committed. This keeps the
  vocab files clean and consistent.

- `/config/kanji-only-vocab.txt` contains a newline-delimited set of vocab for which
  furigana hints are not desired. The Anki deck generation code reads in this file and
  will generate kanji-only cards for any vocab matching these entries in the 'kanji'
  field. If you don't wish to use these settings (or wish to adjust them), empty the
  file or adjust it per your preference. In the future such configuration files will be
  moved outside of version control.

There are other assorted files elsewhere in this repo, but it's mostly legacy garbage
that can be ignored. I'll be removing it and tidying things up as I have the time.

Installation
------------
Les scripts sont écrits en Python 3. Les dépendances s'installent dans un environnement
virtuel (`venv`) placé dans le dossier `python/`, qui est ignoré par git :

```bash
python3 -m venv python
source python/bin/activate
pip install -r requirements.txt
```

Utilisation
-----------
### Principe

Le vocabulaire est rédigé à la main dans des fichiers TOML, puis les scripts de `cardgen/`
le transforment en un paquet Anki (`.apkg`) à importer :

```
vocabulary/**/*.toml  +  config/*.txt  ──►  cardgen/generate_vocabulary_deck.py  ──►  .apkg  ──►  Anki
```

Il est très utile de connaître la différence entre une *note* et une *carte* dans Anki
(voir le manuel d'Anki). Chaque entrée `[[cards]]` d'un fichier TOML devient une **note**,
et chaque note produit plusieurs **cartes** : traduction → japonais, kanji + kana → traduction, etc.

### Générer et importer le deck

**Lancez toujours les scripts depuis la racine du dépôt**, car ils utilisent des chemins
relatifs comme `config/…`, `lists/…` et `vocabulary/…` :

```bash
source python/bin/activate
python cardgen/generate_vocabulary_deck.py   # → japonais_fr.apkg (deck « Japonais généré »)
python cardgen/generate_verb_deck.py         # → japonais_conjugaison_fr.apkg (deck « Japonais généré - conjugaison »)
```

Ensuite, dans Anki : **Fichier → Importer…** et choisissez le fichier `.apkg`.

### Régénérer sans perdre sa progression

Les noms et identifiants du deck et du modèle sont fixes. L'identifiant de chaque note est
calculé à partir de ses champs `kanji` et `kana` uniquement. Vous pouvez donc modifier le
vocabulaire (ajouter, corriger ou retirer des mots, changer les réglages kanji seul), puis
régénérer et réimporter le deck, sans perdre l'historique de révision.

- Modifier n'importe quel champ **autre** que `kanji` et `kana` (traduction, tags,
  niveau…) conserve la progression.
- Modifier le `kanji` ou le `kana` crée une **nouvelle** note : l'historique de l'ancienne
  est perdu.

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
| `python cardgen/insert_blank_notes.py` | Ajoute une entrée vide en tête de chaque fichier pour saisir des mots à la main ; `sort.py` retire celles qui restent vides. |
| `python cardgen/tsv_import.py` | Convertit les fichiers `lists/*.tsv` en fichiers TOML. |
| `python cardgen/generate_verb_deck.py --test` | Lance les tests unitaires du conjugueur. |

### Traduire en français

Le script `cardgen/translation_status.py` sert à suivre et à faire la traduction :

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

Card Templates
--------------

### For all vocab (except verbs)

```toml
[[cards]]
kanji = '' # Kanji. If gairaigo, katakana (which is also duplicated in kana for now).
kana = '' # Hiragana or katakana to function as furigana.
english = '' # English translation. Multiple definitions typically separated with ';'
french = '' # Traduction française, affichée sur les cartes. Sans elle, l'anglais est affiché et la note reçoit le tag 'a_traduire'.
source = '' # Where this vocabulary word originated from
level = 'n[1-5]' # JLPT level: n1, n2, n3, n4, n5. Omitted if not in JLPT.
explain = '' # Optional URL for further reading
tags = [] # grab bag of tags. 'common' is a tag used to denote frequent useage words
```

### For verbs

```toml
[[cards]]
kanji = '' # Kanji. If gairaigo, katakana (which is also duplicated in kana for now).
kana = '' # Hiragana or katakana to function as furigana.
english = ''# English translation. Multiple definitions typically separated with ';'. If transitive, there is a '~' present.
french = '' # Traduction française (infinitif, sans « to »). Garder le '~' si transitif.
english-conjugated = { base = '', past = '', plural = '', continous = '' } # Conjugations
french-conjugated = { infinitif = '', present = '', participe = '', auxiliaire = 'avoir', imperatif = '', nous = '' } # Formes de base pour le deck de conjugaison (voir ci-dessous)
verb-type = '' # ichidan, godan-mu, godan-bu, etc.
transitive = false # whether the verb is transitive or not
level = 'n[1-5]' # JLPT level: n1, n2, n3, n4, n5. Omitted if not in JLPT.
explain = '' # Optional URL for further reading
tags = [] # grab bag of tags. 'common' is a tag used to denote frequent useage words
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

Anki Foo
--------
Search for all _cards_ without a JLPT level,

```
"note:Modèle japonais (FR)" -level:n1 -level:n2 -level:n3 -level:n4 -level:n5 card:1
```

Lister les notes pas encore traduites en français :

```
tag:a_traduire
```

Learning Kanji
--------------
- 2136 Jouyou kanji (elementary and middle school)
  - 1006 taught in primary school (the kyouiku kanji)
  - 1130 taught in secondary school
  - 862 additional kanji allowed for person names (not in Jouyou)

- Wanikani is a useful SRS website that teaches:
  - Kanji: 2027
  - Vocab: 6287

JLPT
----

Levels

- n5: Basic. 800 vocab, 100 kanji. 150 hours of study.
  "Ability to understand some basic Japanese."
- n4: Elementary. 1.5k vocab, 300 kanji. 300 hours.
  "Ability to understand basic Japanese."
- n3: Intermediate. 3.7k vocab, 650 kanji. 450 hours.
  "Ability to understand Japanese used in everyday situations to a certain degree."
- n2: Pre-Advanced. 6k vocab, 1k kanji. 600 hours.
  "Ability to understand Japanese used in everyday situations, and in a variety of
  circumstances to a certain degree."
- n1: Advanced. 10k-18k vocab, 2k kanji. 900 hours.
  "The ability to understand Japanese used in a variety of circumstances."

### JLPT Links

- [JLPT vocabulary lists](https://jlptstudy.net/N5/)
- [Complete list of vocabulary for the JLPT N5](https://nihongoichiban.com/2011/04/30/complete-list-of-vocabulary-for-the-jlpt-n5/)
- [About the JLPT](http://www.tanos.co.uk/jlpt/aboutjlpt/)
- https://www.japanesewithanime.com/2016/10/koitsu-soitsu-aitsu-doitsu-meaning.html

Misc Links
-----

- [jisho.org: Japanese dictionary](https://jisho.org/)
- [Irasshai (Japanese I & II video lectures)](http://www.gpb.org/irasshai)
- [Anime subtitles in Japanese](http://kitsunekko.net/)

License
-------
Public domain.

