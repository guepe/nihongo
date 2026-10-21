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

## Phase 4 : verbes et deck de conjugaison ✅

Finalement, **option A** (formes saisies et stockées) plutôt que `verbecc` : beaucoup de
sens sont des tournures (« aller ensemble », « se réveiller », « montrer du doigt ») qu'un
conjugueur automatique gère mal. Chaque verbe a donc un champ `french-conjugated` (voir
le README) avec ses formes nues : infinitif, présent, participe, auxiliaire, impératifs,
et éventuellement `pronominal` et `complement`. Les 200 verbes sont remplis.

- [x] Méthodes `french_*` dans `generate_verb_deck.py` : négation, élision (n', s', t', d'),
      h aspiré, verbes pronominaux (« s'est levé », « lève-toi ! », « ne te lève pas ! »),
      compléments, et cas particulier des tournures en « être » (« obliger à être là »,
      « subir le fait d'être là »).
- [x] Nouveau deck `1461826981` « Japonais généré - conjugaison » et nouveau modèle
      `1275647302` « Modèle conjugaison japonaise (FR) » ; champs `*_french_*` et
      `base_french` ; 96 cartes aux noms français uniques (« Passé négatif poli : FR → JP »).
- [x] Les cartes FR → JP indiquent « (neutre) » ou « (poli) » ; les deux conditionnels,
      identiques en français, sont distingués par « ～ば » et « ～たら ».
- [x] Le tableau de réponse est en français et affiche bien le groupe du verbe (il
      affichait le kana).
- [x] Fichier de sortie : `japonais_conjugaison_fr.apkg`.
- [x] Tests : les 13 tests anglais sont remplacés par des tests des formes françaises ;
      `test_field_ordering` et `test_field_mapping` réparés. 30 / 30 OK.
- [ ] Limite connue : `VERB_HASH` est indexé par kanji, donc les verbes en double
      (終わる, …) ne donnent qu'une note : 197 notes pour 200 verbes. Ils ont de toute façon
      le même identifiant Anki (kanji + kana + groupe).
- [ ] Le passif des verbes intransitifs reste littéral (« être allé ensemble ») ; en
      japonais, c'est un passif de gêne, rarement utilisé avec ces verbes.

## Phase 5 : scripts d'édition ✅

- [x] `insert_blank_notes.py` : ajoute `('french', '')`, et `french-conjugated` pour les verbes.
- [x] `tsv_import.py` : accepte une 5ᵉ colonne `french` facultative. Il **ajoute** désormais
      les nouveaux mots au fichier `generated_*.toml` au lieu de l'écraser : une relance
      effaçait toutes les notes existantes, traductions comprises.
- [x] `generate_verb_deck.py` ignore, avec un avertissement, un verbe sans
      `french-conjugated` complet.
- [x] `frequency.py`, `update_frequencies.py` : rien à changer, ils ne travaillent que sur le
      japonais.
- [ ] À noter : relancer `tsv_import.py` ajouterait aujourd'hui 2 mots n3, les noms 入学 et
      遠慮. Ils étaient masqués par les verbes du même kanji avant que ceux-ci reçoivent
      leur する. À ajouter et traduire si on les veut.

## Phase 6 : documentation et nettoyage ✅

- [x] `README.md` entièrement en français : présentation du fork, organisation des
      fichiers, installation, utilisation, traduction, conventions, format TOML (avec
      `french` et `french-conjugated`), recherches Anki, kanji, JLPT, liens.
- [x] `book/*.md` traduits (et lecture de 暖かい corrigée : あたたかい).
- [ ] Facultatif : supprimer `english` des TOML, ou le renommer `english_ref`. **Déconseillé**
      pour l'instant : il sert de référence et facilite la reprise des nouveautés du
      projet d'origine.
- [x] `temp/` supprimé (anciens decks `.apkg`, brouillons de vocabulaire et de grammaire
      du projet d'origine ; toujours consultables dans l'historique git).

## Définition de « terminé »

- `python cardgen/translation_status.py` affiche 100 % pour n5 et n4 au minimum.
- Le deck importé dans Anki n'affiche que du français pour les entrées traduites, et
  `tag:a_traduire` liste les entrées restantes.
- Régénérer puis réimporter le deck conserve la progression SRS.
