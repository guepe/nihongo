# Roadmap : passer le deck en français (FR → 日本語)

Objectif : les cartes Anki montrent le **français** à la place de l'anglais. Le japonais
(kanji, kana) ne change pas.

## État des lieux

| Élément | Où | Volume | Contient de l'anglais ? |
|---|---|---|---|
| Vocabulaire, champ `english` | `vocabulary/**/*.toml` (76 fichiers) | 3 206 entrées | **Oui, c'est le cœur du travail** |
| Conjugaisons, champ `english-conjugated` | `vocabulary/verbs/*.toml` | 200 verbes | Oui (`base`, `past`, `plural`, `continuous`) |
| Templates du deck vocabulaire | `cardgen/generate_vocabulary_deck.py` | 3 templates, 10 champs | Noms de champs (`English`), noms de cartes |
| Deck de conjugaison | `cardgen/generate_verb_deck.py` | ~15 formes | **Oui : la grammaire anglaise est codée en dur** (`will …`, `let's …`, `didn't …`) |
| Scripts d'édition | `tsv_import.py`, `insert_blank_notes.py` | 2 scripts | Créent des clés `english` |
| Notes de cours | `book/*.md` | 5 fichiers, ~200 lignes | Oui |
| README | `README.md` | 1 fichier | Oui |
| Listes de fréquence / JLPT | `lists/` | – | Non : seul le japonais est utilisé. **On n'y touche pas** |
| `tags`, `level`, `source` | toml | – | Clés techniques, invisibles sur les cartes. **On les garde tels quels** |
| `temp/` | – | – | Déchets d'origine, ignorés par les scripts |

Quelques caractéristiques des données, à respecter pendant la traduction :

- Les `kanji` + `kana` déterminent l'ID de la note. Modifier le texte anglais ou français
  ne fait donc **jamais** perdre la progression SRS.
- Environ 640 entrées ont plusieurs sens, séparés par `;` ou `,`.
- 111 entrées contiennent `~`, qui signale un verbe transitif ou une particule à compléter.
- Beaucoup d'entrées ont une précision entre parenthèses, par exemple
  `'tonight (more formal / in writing)'`.
- Répartition JLPT : n5 = 721, n4 = 575, n3 = 1 568, n2 = 87, n1 = 66. Le reste n'a pas de niveau.
- Plus gros fichiers : `generated_jlpt_n3_wiktionary.toml` (1 324),
  `misc.toml` (314), `generated_jlpt_n5_n4_wiktionary.toml` (195), `verbs/verbs.toml` (161).

## Choix de conception

**On ajoute un champ `french` au lieu d'écraser `english`.**

```toml
[[cards]]
kanji = '今晩'
kana = 'こんばん'
english = 'tonight (more formal / in writing)'
french = 'ce soir (plus soutenu / à l\'écrit)'
```

Raisons :
- La traduction peut se faire progressivement : un mot sans `french` reste utilisable.
- L'anglais sert de référence pour vérifier le sens, et de secours tant que le français manque.
- On peut toujours faire un `diff` avec le repo d'origine pour récupérer ses nouveaux mots.

Règle du générateur : afficher `french` s'il existe, sinon `english`, et ajouter le tag
`a_traduire` à la note. Une recherche `tag:a_traduire` dans Anki liste alors ce qui reste à faire.

On pourra supprimer `english` à la toute fin (phase 6), si on le souhaite.

---

## Phase 0 : préparation

- [x] Supprimer les deux lignes `for card in note.cards: card.suspend = True` dans
      `generate_vocabulary_deck.py`. Ce code suspendait 100 % des cartes générées ; il ne
      reste plus que les 12 cartes de `config/suspended.txt`.
- [x] Commiter le `requirements.txt` mis à jour (genanki 0.13.1, toml 0.10.2) et le correctif
      `cached_property`.
- [x] `generate_verb_deck.py` plantait avec genanki 0.13, qui refuse les champs `None`
      (verbes sans niveau JLPT) : ces champs sont maintenant convertis en `''`.
- [x] Ajouter `verb_card_deck_output.apkg` au `.gitignore`.
- [x] Vérifier que `sort.py` / `library.py` gèrent `french`. Ils conservent l'ordre des clés
      du fichier, donc il n'y a rien à modifier : `french` reste là où on l'écrit.
      `sort.py` ne modifie aucun fichier existant.
- [ ] (Phase 4) Les tests `test_field_ordering` et `test_field_mapping` échouent depuis 2019 :
      ils ne connaissent pas les champs `*_english_*`. À réécrire avec les champs français.

## Phase 1 : deck vocabulaire en français (code) ✅

Dans `cardgen/generate_vocabulary_deck.py` :

- [x] Lire `french`, avec repli sur `english` et le tag `a_traduire` si le français manque.
- [x] **Nouveau deck et nouveau modèle Anki.** Aucun deck n'avait été importé, donc on part
      de zéro avec de nouveaux IDs, figés :
      - deck `2080406641` : `Japonais généré`
      - modèle `1405375075` : `Modèle japonais (FR)`
      - champs : `Kanji`, `Kana`, `Français`, `Carte furigana ?`, `Carte kanji seul ?`,
        `Carte kana seul ?`, `Niveau`, `Fréquence max`, `Source fréquence`, `Fréquence anime`
      - cartes : `Français → Japonais`, `Kanji + Kana`, `Kanji seul (optionnel)`,
        `Kana seul (optionnel)`
- [x] Templates traduits (`(anime)` reste tel quel).
- [x] Le résumé final affiche `notes translated to French: X / Y`.
- [x] Fichier de sortie : `japonais_fr.apkg` (ignoré par git).
- [x] README : schéma TOML avec `french`, recherche `tag:a_traduire`.

> ⚠️ À partir de maintenant, **ne plus changer** les IDs, l'ordre des champs ni les noms
> de champs et de cartes sans passer d'abord par l'interface d'Anki : le deck va être
> importé, et une modification ferait perdre la progression ou créerait un modèle en double.

## Phase 2 : outil de suivi ✅

- [x] `cardgen/translation_status.py` (voir la section « Traduire en français » du README) :
  - sans option : avancement par fichier et par niveau JLPT ;
  - `--missing [--level n5] [--limit 50]` : mots sans `french` ;
  - `--export fichier.tsv [--level n5] [--limit N] [--all]` /
    `--import fichier.tsv` : aller-retour par tableur ou par LLM. Chaque mot est identifié
    par `kanji` + `kana` + `english` : il y a 24 doublons kanji+kana, dont certains avec
    des sens différents. Seules les lignes `french` changent dans les fichiers TOML.

## Phase 3 : traduction du vocabulaire (données) ✅

Les 3 198 notes actives sont traduites (premier jet relu par échantillonnage). Le lot 1
(200 mots n5) a été validé à la main ; le reste a été traduit en 8 paquets avec les
mêmes conventions, puis contrôlé automatiquement : alignement des lignes, aucune case
vide, aucun reste d'anglais.

- [x] **n5** (721)
- [x] **n4** (575)
- [x] **n3** (1 566)
- [x] n2, n1, puis les entrées sans niveau

Quand l'anglais était faux ou incomplet, la traduction suit le japonais. Exemples :
匂い → « odeur; parfum » (l'anglais disait « mauvaise odeur ») ; 自身 → « soi-même »
(l'anglais disait « self-confidence », qui est 自信) ; 変化 (へんか) → « changement ».

### Erreurs corrigées dans les données d'origine ✅

Corrigées avant le premier import dans Anki (l'identifiant d'une note dépend de son
kanji et de son kana) :

- [x] `さ` / きょか → 許可 ; `お` / じき → 直
- [x] 思い出 : `おもで` → おもいで ; 宜しい / よろしい : kanji et kana remis dans le bon sens
- [x] 13 mots dont le kana finissait par する sans que le kanji le fasse (遠慮, 故障, 退院,
      入学, 拝見, 出席, 承知, 食事, 世話, 輸出, 経験…) : `する` ajouté au kanji ;
      相談 : kana « そうだん / そうだんする » → そうだん
- [x] 自身 « self-confidence » (manga-and-anime) → kanji 自信, « confiance en soi »
- [x] 用 (よう) : les deux notes sont fusionnées en une seule (« task; business »)
- [x] `update_frequencies.py` cherche aussi les verbes en する sous leur forme nom

Conventions de traduction :

| Cas | Anglais | Français |
|---|---|---|
| Un seul sens, le plus courant | `ability` | `capacité` |
| Plusieurs sens | `comprehension, understanding` | `compréhension` (garder une seule traduction quand c'est possible, comme le préconise le README) |
| Verbe | `to raise` | `lever` (infinitif sans « to ») |
| Transitif `~` | `~ to open` | `ouvrir ~` (garder le `~`) |
| Précision | `(literary)` | `(littéraire)` |
| Registre | `(formal)`, `(casual)` | `(soutenu)`, `(familier)` |
| Nom | `paragraph` | `paragraphe` (sans article, sauf s'il faut lever une ambiguïté de genre) |
| Adjectif | `big` | `grand` (masculin singulier) |
| Mot d'emprunt (gairaigo) | `motorcycle` | `moto` |

- [ ] Mettre ces conventions dans le README une fois qu'elles sont validées.
- [ ] Les 54 liens `explain` pointent vers des sites anglophones. On les laisse : ils restent utiles.

## Phase 4 : verbes et deck de conjugaison

C'est la partie la plus délicate. L'anglais forme ses temps avec des auxiliaires
(`will`, `didn't`, `can`), ce que le code exploite en assemblant
`base / past / plural / continuous`. Le français a besoin de vraies formes conjuguées.

Options :

| Option | Principe | Avantage | Inconvénient |
|---|---|---|---|
| **A. Formes saisies à la main** | `french-conjugated = { infinitif, present, passe, futur, participe, imperatif }` à la 3ᵉ personne (« il mange », « il a mangé ») | Contrôle total | ~200 × 6 formes à saisir |
| **B. Conjugueur automatique** | Bibliothèque Python [`verbecc`](https://pypi.org/project/verbecc/) pour générer les formes depuis l'infinitif | Presque rien à saisir | Dépendance de plus ; choix de l'auxiliaire et cas pronominaux à vérifier |
| **C. Tournures à l'infinitif** | `ne pas ~`, `pouvoir ~`, `faire ~`, `être ~é` | Seul l'infinitif est nécessaire | Moins naturel pour le présent, le passé et le volitif |

**Recommandation : B avec A en secours.** Le script conjugue avec `verbecc`, et un champ
`french-conjugated` facultatif permet de corriger un cas particulier à la main.

Correspondance des formes japonaises (voir les méthodes `english_*` de `generate_verb_deck.py`) :

| Forme | Exemple EN actuel | FR proposé |
|---|---|---|
| present_indicative | will eat / won't eat | (il) mange / ne mange pas |
| presumptive | will probably eat | va sans doute manger |
| volitional | let's eat | mangeons ! |
| imperative | eat! / don't eat! | mange ! / ne mange pas ! |
| past_indicative | ate / didn't eat | a mangé / n'a pas mangé |
| past_presumptive | probably ate | a sans doute mangé |
| present_progressive | eating / not eating | est en train de manger / ne mange pas |
| past_progressive | was eating | était en train de manger |
| provisional / conditional | if one eats | si on mange / si on ne mange pas |
| potential | can eat | peut manger / ne peut pas manger |
| causative | make eat | faire manger |
| passive | be eaten | être mangé |

- [ ] Réécrire les méthodes `english_*` en `french_*` (en gardant les noms de champs Anki
      existants, ou avec de nouveaux IDs comme en phase 1 si on part de zéro).
- [ ] Adapter `generate_verb_deck_tests.py`, puis lancer `python cardgen/generate_verb_deck.py --test`.
- [ ] Traduire `english` (le résumé) des 200 verbes, comme en phase 3.

## Phase 5 : scripts d'édition

- [ ] `insert_blank_notes.py` : ajouter `('french', '')` (et `french-conjugated` pour les verbes).
- [ ] `tsv_import.py` : accepter une colonne `french` facultative.
- [ ] `frequency.py`, `update_frequencies.py` : rien à changer, ils ne travaillent que sur le japonais.

## Phase 6 : documentation et nettoyage

- [ ] Réécrire le `README.md` en français : installation, utilisation, schéma toml avec
      `french`, conventions de traduction.
- [ ] Traduire `book/*.md` (~200 lignes).
- [ ] Facultatif : une fois tout traduit, supprimer `english` des toml, ou le renommer en
      `english_ref` pour garder la référence.
- [ ] Facultatif : supprimer `temp/` et les autres reliquats signalés dans le README.

## Définition de « terminé »

- `python cardgen/translation_status.py` affiche 100 % pour n5 et n4 au minimum.
- Le deck importé dans Anki n'affiche que du français pour les entrées traduites, et
  `tag:a_traduire` liste les entrées restantes.
- Régénérer puis réimporter le deck conserve la progression SRS.
