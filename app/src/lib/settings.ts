import { LEVELS, NO_LEVEL, type ReviewCard } from './cards'
import type { DeckId } from './types'

export interface Settings {
  decks: Record<DeckId, { enabled: boolean; newPerDay: number }>
  levels: string[] // studied levels, including NO_LEVEL
  conjugations: string[] // ids of the enabled conjugations
  retention: number // FSRS desired retention, 0.7 – 0.97
}

export const DEFAULT_SETTINGS: Settings = {
  decks: {
    vocabulary: { enabled: true, newPerDay: 15 },
    conjugation: { enabled: true, newPerDay: 5 },
  },
  levels: [...LEVELS, NO_LEVEL],
  conjugations: ['present_indicative', 'past_indicative'],
  retention: 0.9,
}

/** Fills in settings saved by an older version of the app. */
export function withDefaults(saved: Partial<Settings> | undefined): Settings {
  return {
    ...DEFAULT_SETTINGS,
    ...saved,
    decks: { ...DEFAULT_SETTINGS.decks, ...saved?.decks },
  }
}

export function isStudied(card: ReviewCard, settings: Settings): boolean {
  if (!settings.decks[card.deck].enabled) return false
  if (!settings.levels.includes(card.level)) return false
  if (card.deck === 'conjugation' && !settings.conjugations.includes(card.conjugation.id)) {
    return false
  }
  return true
}
