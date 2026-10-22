// Structure of public/deck.json, produced by cardgen/export_json.py (see roadmap-app.md).

export const DECK_FORMAT = 1

export interface DeckFile {
  format: number
  version: string
  decks: {
    vocabulary: VocabularyDeck
    conjugation: ConjugationDeck
  }
}

export interface Frequency {
  score: number
  source: string
  anime?: number
}

export interface VocabularyNote {
  id: string
  kanji: string
  kana: string
  romaji: string
  french: string
  level: string | null
  tags: string[]
  frequency: Frequency | null
  suspended: boolean
  cards: VocabularyCardType[]
}

export type VocabularyCardType = 'fr-jp' | 'furigana' | 'kanji' | 'kana'

export interface VocabularyDeck {
  name: string
  card_types: { id: VocabularyCardType; label: string }[]
  notes: VocabularyNote[]
}

export interface ConjugatedForm {
  kanji: string
  kana: string
  romaji: string
  french: string
}

export interface Conjugation {
  id: string
  label: string
  hint: string | null
  forms: string[] // 'plain.positive', 'polite.negative'…
}

export interface VerbNote {
  id: string
  kanji: string
  kana: string
  romaji: string
  french: string
  group: string
  level: string | null
  forms: Record<string, ConjugatedForm> // key: '<conjugation>.<register>.<polarity>'
}

export type Direction = 'fr-jp' | 'jp-fr'

export interface ConjugationDeck {
  name: string
  directions: Direction[]
  conjugations: Conjugation[]
  notes: VerbNote[]
}

export type DeckId = 'vocabulary' | 'conjugation'
