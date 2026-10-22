// Turns deck.json notes into the list of cards that can be reviewed.

import type {
  Conjugation, ConjugatedForm, DeckFile, DeckId, Direction, VerbNote, VocabularyCardType,
  VocabularyNote,
} from './types'

export const LEVELS = ['n5', 'n4', 'n3', 'n2', 'n1'] as const
export const NO_LEVEL = 'none'

interface BaseCard {
  key: string // unique: '<note id> <card type>' (note ids never contain spaces)
  deck: DeckId
  noteId: string
  type: string
  // Cards of the same group are not shown on the same day: the second one would be too
  // easy right after the first. One group per word, and per conjugated form for verbs.
  sibling: string
  level: string // 'n5'…'n1', or NO_LEVEL
  order: number // position among new cards of its deck
}

export interface VocabularyCard extends BaseCard {
  deck: 'vocabulary'
  type: VocabularyCardType
  note: VocabularyNote
}

export interface ConjugationCard extends BaseCard {
  deck: 'conjugation'
  note: VerbNote
  conjugation: Conjugation
  form: ConjugatedForm
  register: 'plain' | 'polite'
  polarity: 'positive' | 'negative'
  direction: Direction
}

export type ReviewCard = VocabularyCard | ConjugationCard

export function cardKey(noteId: string, type: string): string {
  return noteId + ' ' + type
}

function levelRank(level: string | null): number {
  const index = LEVELS.indexOf(level as (typeof LEVELS)[number])
  return index === -1 ? LEVELS.length : index
}

export function buildCards(deck: DeckFile): ReviewCard[] {
  const cards: ReviewCard[] = []

  // New vocabulary: easiest level first, then the most frequent words.
  const vocabulary = [...deck.decks.vocabulary.notes].sort((a, b) =>
    levelRank(a.level) - levelRank(b.level)
    || (a.frequency?.score ?? Infinity) - (b.frequency?.score ?? Infinity)
    || a.id.localeCompare(b.id))
  let order = 0
  for (const note of vocabulary) {
    if (note.suspended) continue
    for (const type of note.cards) {
      cards.push({
        key: cardKey(note.id, type), deck: 'vocabulary', noteId: note.id, type, sibling: note.id,
        level: note.level ?? NO_LEVEL, order: order++, note,
      })
    }
  }

  // New conjugations: easiest verbs first, each verb through every form.
  const { conjugations, directions } = deck.decks.conjugation
  const verbs = [...deck.decks.conjugation.notes].sort((a, b) =>
    levelRank(a.level) - levelRank(b.level) || a.kana.localeCompare(b.kana, 'ja'))
  order = 0
  for (const note of verbs) {
    for (const conjugation of conjugations) {
      for (const formId of conjugation.forms) {
        const form = note.forms[conjugation.id + '.' + formId]
        if (!form) continue
        const [register, polarity] = formId.split('.') as ['plain' | 'polite', 'positive' | 'negative']
        for (const direction of directions) {
          const type = `${conjugation.id}.${formId}.${direction}`
          cards.push({
            key: cardKey(note.id, type), deck: 'conjugation', noteId: note.id, type,
            sibling: cardKey(note.id, `${conjugation.id}.${formId}`),
            level: note.level ?? NO_LEVEL, order: order++, note, conjugation, form, register,
            polarity, direction,
          })
        }
      }
    }
  }

  return cards
}
