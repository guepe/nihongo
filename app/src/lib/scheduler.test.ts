import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { Rating, State } from 'ts-fsrs'

import { buildCards } from './cards'
import { Scheduler, endOfStudyDay, startOfStudyDay, type ReviewEvent } from './scheduler'
import { DEFAULT_SETTINGS, type Settings } from './settings'
import type { DeckFile } from './types'

const deck: DeckFile = JSON.parse(readFileSync(new URL('../../public/deck.json', import.meta.url), 'utf-8'))
const cards = buildCards(deck)
const DEVICE = 'test'
const MINUTE = 60 * 1000
const DAY = 24 * 60 * MINUTE
// Wednesday 22 October 2026, 10:00 local time.
const NOW = new Date(2026, 9, 22, 10, 0).getTime()

function settings(overrides: Partial<Settings> = {}): Settings {
  return { ...structuredClone(DEFAULT_SETTINGS), ...overrides }
}

describe('cards', () => {
  it('builds every card of deck.json', () => {
    const vocabulary = deck.decks.vocabulary.notes
      .filter((n) => !n.suspended)
      .reduce((sum, n) => sum + n.cards.length, 0)
    const conjugation = deck.decks.conjugation.notes
      .reduce((sum, n) => sum + Object.keys(n.forms).length * 2, 0)
    expect(cards.length).toBe(vocabulary + conjugation)
    expect(new Set(cards.map((c) => c.key)).size).toBe(cards.length)
  })

  it('starts new vocabulary with frequent n5 words', () => {
    const first = cards.filter((c) => c.deck === 'vocabulary').sort((a, b) => a.order - b.order)[0]
    expect(first.level).toBe('n5')
  })
})

describe('study day', () => {
  it('starts at 4 a.m.', () => {
    const lateNight = new Date(2026, 9, 23, 1, 30).getTime()
    expect(startOfStudyDay(lateNight)).toBe(new Date(2026, 9, 22, 4, 0).getTime())
    expect(endOfStudyDay(NOW)).toBe(new Date(2026, 9, 23, 4, 0).getTime())
  })
})

describe('Scheduler', () => {
  it('shows new cards up to the daily limit of each deck', () => {
    const s = settings()
    const scheduler = new Scheduler(cards, [], s.retention)
    expect(scheduler.counts(s, NOW)).toEqual({
      vocabulary: { learning: 0, review: 0, new: 15 },
      conjugation: { learning: 0, review: 0, new: 5 },
    })

    let now = NOW
    const seen = new Set<string>()
    for (let card = scheduler.next(s, now); card; card = scheduler.next(s, now)) {
      seen.add(card.key)
      scheduler.answer(card, Rating.Easy, now, DEVICE) // Easy: straight to review, not today
      now += MINUTE
    }
    expect(seen.size).toBe(20)
    expect([...seen].filter((k) => cards.find((c) => c.key === k)!.deck === 'conjugation').length).toBe(5)
  })

  it('brings back a failed card a minute later', () => {
    const s = settings()
    const scheduler = new Scheduler(cards, [], s.retention)
    const card = scheduler.next(s, NOW)!
    scheduler.answer(card, Rating.Again, NOW, DEVICE)
    expect(scheduler.state(card)!.state).toBe(State.Learning)
    expect(scheduler.next(s, NOW)!.key).not.toBe(card.key) // other new cards first
    expect(scheduler.next(s, NOW + 2 * MINUTE)!.key).toBe(card.key)
  })

  it('gives the same result when replaying saved events', () => {
    const s = settings()
    const live = new Scheduler(cards, [], s.retention)
    const events: ReviewEvent[] = []
    let now = NOW
    for (let day = 0; day < 10; day++) {
      for (let card = live.next(s, now); card; card = live.next(s, now)) {
        // Hard on a learning card keeps it learning: only use it for reviews.
        const reviewing = live.state(card)?.state === State.Review
        const rating = reviewing && card.order % 3 === 0 ? Rating.Hard : Rating.Good
        events.push(live.answer(card, rating, now, DEVICE))
        now += MINUTE
      }
      now = startOfStudyDay(now) + DAY + 6 * 60 * MINUTE // next day, 10:00
    }
    // Events from several devices arrive in any order.
    const replayed = new Scheduler(cards, [...events].reverse(), s.retention)
    for (const card of cards) {
      expect(replayed.state(card)?.due.getTime()).toBe(live.state(card)?.due.getTime())
    }
    expect(replayed.counts(s, now)).toEqual(live.counts(s, now))
  })

  it('undoes the last answer, also after a reload', () => {
    const s = settings()
    const scheduler = new Scheduler(cards, [], s.retention)
    const first = scheduler.next(s, NOW)!
    const answer = scheduler.answer(first, Rating.Good, NOW, DEVICE)
    const undo = scheduler.undo(NOW + MINUTE, DEVICE)!
    expect(undo.card.key).toBe(first.key)
    expect(undo.event.target).toBe(answer.id)
    expect(scheduler.state(first)).toBeUndefined()
    expect(scheduler.next(s, NOW + MINUTE)!.key).toBe(first.key)

    const reloaded = new Scheduler(cards, [answer, undo.event], s.retention)
    expect(reloaded.state(first)).toBeUndefined()
    expect(reloaded.counts(s, NOW).vocabulary.new).toBe(15)
  })

  it('shows the other direction of a word on the next day', () => {
    const s = settings()
    const scheduler = new Scheduler(cards, [], s.retention)
    const shown: string[] = []
    let now = NOW
    for (let card = scheduler.next(s, now); card; card = scheduler.next(s, now)) {
      shown.push(card.key)
      scheduler.answer(card, Rating.Easy, now, DEVICE)
      now += MINUTE
    }
    const firstDay = shown.map((key) => cards.find((c) => c.key === key)!)
    expect(new Set(firstDay.map((c) => c.sibling)).size).toBe(firstDay.length)

    const tomorrow = startOfStudyDay(now) + DAY + 6 * 60 * MINUTE
    const next = scheduler.next(s, tomorrow)!
    expect(next.sibling).toBe(firstDay[0].sibling)
    expect(next.key).not.toBe(firstDay[0].key)
  })

  it('only studies the enabled decks, levels and conjugations', () => {
    const s = settings({ levels: ['n5'], conjugations: ['potential'] })
    s.decks.vocabulary.enabled = false
    const scheduler = new Scheduler(cards, [], s.retention)
    for (let i = 0; i < 5; i++) {
      const card = scheduler.next(s, NOW)!
      expect(card.deck).toBe('conjugation')
      expect(card.level).toBe('n5')
      if (card.deck === 'conjugation') expect(card.conjugation.id).toBe('potential')
      scheduler.answer(card, Rating.Easy, NOW, DEVICE)
    }
    expect(scheduler.next(s, NOW)).toBeNull()
  })
})

describe('statistics', () => {
  it('counts answers per day, the streak and the retention', async () => {
    const { computeStats } = await import('./stats')
    const s = settings()
    const scheduler = new Scheduler(cards, [], s.retention)
    let now = NOW
    for (let day = 0; day < 5; day++) {
      for (let card = scheduler.next(s, now); card; card = scheduler.next(s, now)) {
        // Fail some reviews, but never a card being relearnt (it would come back forever).
        const reviewing = scheduler.state(card)?.state === State.Review
        scheduler.answer(card, reviewing && card.order % 4 === 0 ? Rating.Again : Rating.Good, now, DEVICE)
        now += MINUTE
      }
      now = startOfStudyDay(now) + DAY + 6 * 60 * MINUTE
    }
    const stats = computeStats(scheduler, s, now)
    expect(stats.perDay).toHaveLength(30)
    expect(stats.perDay.slice(-6, -1).every((d) => d.count > 0)).toBe(true)
    expect(stats.reviewsToday).toBe(0)
    expect(stats.streak).toBe(5) // nothing yet today: the streak still counts
    expect(stats.retention).toBeGreaterThan(0)
    expect(stats.retention).toBeLessThan(1)
    expect(stats.learned).toBeGreaterThan(0)
    expect(stats.learning + stats.learned).toBeLessThanOrEqual(stats.seen)
    expect(stats.forecast).toHaveLength(14)
    expect(stats.forecast.reduce((sum, d) => sum + d.count, 0)).toBeGreaterThan(0)
  })

  it('ignores answers to cards removed from the deck', () => {
    const removed: ReviewEvent = { id: '00000000-0000-4000-8000-000000000000', kind: 'review', at: NOW, device: DEVICE, deck: 'vocabulary', note: 'gone', card: 'fr-jp', rating: 3 }
    const scheduler = new Scheduler(cards, [removed], 0.9)
    expect(scheduler.history().size).toBe(0)
    expect(scheduler.undo(NOW, DEVICE)).toBeNull()
  })
})
