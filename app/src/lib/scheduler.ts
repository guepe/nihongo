// Review scheduling with FSRS. The progress of a card is never stored: it is recomputed by
// replaying its review events, so that events from several devices can simply be merged.

import { createEmptyCard, fsrs, generatorParameters, State, type Card, type FSRS, type Grade } from 'ts-fsrs'

import { cardKey, type ReviewCard } from './cards'
import { isStudied, type Settings } from './settings'
import type { DeckId } from './types'

export interface ReviewEvent {
  id: string // UUID, so that sending an event twice is harmless
  kind: 'review' | 'undo'
  at: number // milliseconds since 1970
  device: string
  // kind = 'review'
  deck?: DeckId
  note?: string
  card?: string
  rating?: Grade
  // kind = 'undo': id of the cancelled review
  target?: string
}

// Like Anki, a study day starts at 4 a.m.: reviewing at 1 a.m. still counts for the evening.
export const DAY_START_HOUR = 4
// Learning cards due within this delay may be shown early when nothing else is left.
export const LEARN_AHEAD_MS = 20 * 60 * 1000

export function startOfStudyDay(now: number): number {
  const day = new Date(now - DAY_START_HOUR * 3600 * 1000)
  day.setHours(DAY_START_HOUR, 0, 0, 0)
  return day.getTime()
}

export function endOfStudyDay(now: number): number {
  const day = new Date(startOfStudyDay(now))
  day.setDate(day.getDate() + 1)
  return day.getTime()
}

export function uuid(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  // crypto.randomUUID only exists on https and localhost; this covers tests over the LAN.
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

export interface DeckCounts {
  learning: number
  review: number
  new: number
}

export function isLearning(card: Card): boolean {
  return card.state === State.Learning || card.state === State.Relearning
}

export class Scheduler {
  private readonly fsrs: FSRS
  private readonly cards = new Map<string, ReviewCard>()
  private readonly reviews = new Map<string, ReviewEvent[]>() // per card, oldest first
  private readonly states = new Map<string, Card>()
  private readonly undone = new Set<string>()

  constructor(cards: ReviewCard[], events: ReviewEvent[], retention: number) {
    this.fsrs = fsrs(generatorParameters({ request_retention: retention, enable_fuzz: true }))
    for (const card of cards) this.cards.set(card.key, card)
    for (const event of events) {
      if (event.kind === 'undo' && event.target) this.undone.add(event.target)
    }
    const sorted = events.filter((e) => e.kind === 'review').sort((a, b) => a.at - b.at)
    for (const event of sorted) {
      if (this.undone.has(event.id)) continue
      const key = cardKey(event.note!, event.card!)
      const list = this.reviews.get(key) ?? []
      list.push(event)
      this.reviews.set(key, list)
    }
    for (const key of this.reviews.keys()) this.replay(key)
  }

  private replay(key: string) {
    const events = this.reviews.get(key)
    if (!events?.length) {
      this.states.delete(key)
      return
    }
    let card = createEmptyCard(events[0].at)
    for (const event of events) card = this.fsrs.next(card, event.at, event.rating!).card
    this.states.set(key, card)
  }

  state(card: ReviewCard): Card | undefined {
    return this.states.get(card.key)
  }

  /** The next due date of the card for each possible answer. */
  preview(card: ReviewCard, now: number): Record<Grade, Date> {
    const outcomes = this.fsrs.repeat(this.states.get(card.key) ?? createEmptyCard(now), now)
    return {
      1: outcomes[1].card.due, 2: outcomes[2].card.due,
      3: outcomes[3].card.due, 4: outcomes[4].card.due,
    }
  }

  /** Records an answer. The returned event must be saved by the caller. */
  answer(card: ReviewCard, rating: Grade, now: number, device: string): ReviewEvent {
    const event: ReviewEvent = {
      id: uuid(), kind: 'review', at: now, device,
      deck: card.deck, note: card.noteId, card: card.type, rating,
    }
    const list = this.reviews.get(card.key) ?? []
    list.push(event)
    this.reviews.set(card.key, list)
    this.replay(card.key)
    return event
  }

  /** Cancels the most recent answer. Returns the undo event to save and the card to show again. */
  undo(now: number, device: string): { event: ReviewEvent; card: ReviewCard } | null {
    let latest: ReviewEvent | undefined
    let latestKey = ''
    for (const [key, events] of this.reviews) {
      const last = events[events.length - 1]
      if (last && (!latest || last.at > latest.at)) {
        latest = last
        latestKey = key
      }
    }
    const card = this.cards.get(latestKey)
    if (!latest || !card) return null
    this.reviews.get(latestKey)!.pop()
    this.undone.add(latest.id)
    this.replay(latestKey)
    return { event: { id: uuid(), kind: 'undo', at: now, device, target: latest.id }, card }
  }

  /** Number of cards of each deck seen for the first time today. */
  private introducedToday(now: number): Record<DeckId, number> {
    const start = startOfStudyDay(now)
    const counts: Record<DeckId, number> = { vocabulary: 0, conjugation: 0 }
    for (const [key, events] of this.reviews) {
      const card = this.cards.get(key)
      if (card && events.length && events[0].at >= start) counts[card.deck]++
    }
    return counts
  }

  private newRemaining(settings: Settings, now: number): Record<DeckId, number> {
    const introduced = this.introducedToday(now)
    return {
      vocabulary: Math.max(0, settings.decks.vocabulary.newPerDay - introduced.vocabulary),
      conjugation: Math.max(0, settings.decks.conjugation.newPerDay - introduced.conjugation),
    }
  }

  counts(settings: Settings, now: number): Record<DeckId, DeckCounts> {
    const end = endOfStudyDay(now)
    const counts: Record<DeckId, DeckCounts> = {
      vocabulary: { learning: 0, review: 0, new: 0 },
      conjugation: { learning: 0, review: 0, new: 0 },
    }
    for (const card of this.cards.values()) {
      if (!isStudied(card, settings)) continue
      const state = this.states.get(card.key)
      if (!state) counts[card.deck].new++
      else if (state.due.getTime() < end) {
        if (isLearning(state)) counts[card.deck].learning++
        else counts[card.deck].review++
      }
    }
    const remaining = this.newRemaining(settings, now)
    for (const deck of ['vocabulary', 'conjugation'] as DeckId[]) {
      counts[deck].new = Math.min(counts[deck].new, remaining[deck])
    }
    return counts
  }

  /**
   * The card to show now, or null when the day is done. Order: learning cards that are due,
   * then reviews, then new cards, then learning cards due in the next few minutes.
   */
  next(settings: Settings, now: number): ReviewCard | null {
    const end = endOfStudyDay(now)
    const remaining = this.newRemaining(settings, now)
    let learning: ReviewCard | null = null
    let learningDue = Infinity
    let review: ReviewCard | null = null
    let reviewDue = Infinity
    const fresh: Partial<Record<DeckId, ReviewCard>> = {}

    for (const card of this.cards.values()) {
      if (!isStudied(card, settings)) continue
      const state = this.states.get(card.key)
      if (!state) {
        const best = fresh[card.deck]
        if (remaining[card.deck] > 0 && (!best || card.order < best.order)) fresh[card.deck] = card
        continue
      }
      const due = state.due.getTime()
      if (isLearning(state)) {
        if (due < learningDue) {
          learning = card
          learningDue = due
        }
      } else if (due < end && due < reviewDue) {
        review = card
        reviewDue = due
      }
    }

    if (learning && learningDue <= now) return learning
    if (review) return review
    // Alternate between decks: take the one with the most new cards left for today.
    const newCards = (['vocabulary', 'conjugation'] as DeckId[])
      .filter((deck) => fresh[deck])
      .sort((a, b) => remaining[b] - remaining[a])
    if (newCards.length) return fresh[newCards[0]]!
    if (learning && learningDue <= now + LEARN_AHEAD_MS) return learning
    return null
  }

  /** When the next learning card is due, if any is due later today. */
  nextLearningDue(settings: Settings, now: number): number | null {
    const end = endOfStudyDay(now)
    let next: number | null = null
    for (const [key, state] of this.states) {
      const card = this.cards.get(key)
      if (!card || !isStudied(card, settings) || !isLearning(state)) continue
      const due = state.due.getTime()
      if (due < end && (next === null || due < next)) next = due
    }
    return next
  }
}
