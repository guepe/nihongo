// Figures of the statistics screen, computed from the answers kept by the scheduler.

import { State } from 'ts-fsrs'

import { endOfStudyDay, isLearning, startOfStudyDay, type Scheduler } from './scheduler'
import type { Settings } from './settings'

const DAY = 24 * 60 * 60 * 1000
// A card answered after at least this long tests memory, not short-term recall.
const SPACED = 20 * 60 * 60 * 1000
// A card whose memory lasts this long is considered mastered (Anki's "mature").
const MASTERED_DAYS = 21

export interface DayCount {
  day: number // start of the study day (ms)
  count: number
}

export interface Stats {
  reviewsToday: number
  streak: number // consecutive study days with at least one answer
  retention: number | null // share of spaced answers that weren't "À revoir", last 30 days
  spacedAnswers: number
  seen: number
  learning: number
  learned: number
  mastered: number
  perDay: DayCount[] // last 30 study days, oldest first
  forecast: DayCount[] // reviews due in the next 14 study days, today first
}

/** Start of each study day, from `from` for `count` days (handles daylight saving time). */
function days(from: number, count: number): number[] {
  const result: number[] = []
  let day = startOfStudyDay(from)
  for (let i = 0; i < count; i++) {
    result.push(day)
    day = endOfStudyDay(day)
  }
  return result
}

export function computeStats(scheduler: Scheduler, settings: Settings, now: number): Stats {
  const today = startOfStudyDay(now)
  const monthStart = startOfStudyDay(now - 29 * DAY)
  const perDay = new Map(days(monthStart, 30).map((day) => [day, 0]))
  const activeDays = new Set<number>()
  let spaced = 0
  let remembered = 0

  for (const events of scheduler.history().values()) {
    events.forEach((event, i) => {
      const day = startOfStudyDay(event.at)
      activeDays.add(day)
      if (perDay.has(day)) perDay.set(day, perDay.get(day)! + 1)
      if (i > 0 && event.at >= monthStart && event.at - events[i - 1].at >= SPACED) {
        spaced++
        if (event.rating! > 1) remembered++
      }
    })
  }

  // Today without answers yet doesn't break the streak.
  let streak = 0
  let day = activeDays.has(today) ? today : startOfStudyDay(today - DAY)
  while (activeDays.has(day)) {
    streak++
    day = startOfStudyDay(day - DAY)
  }

  const forecastDays = days(now, 14)
  const forecast = new Map(forecastDays.map((d) => [d, 0]))
  const horizon = endOfStudyDay(forecastDays[forecastDays.length - 1])
  let seen = 0
  let learning = 0
  let learned = 0
  let mastered = 0
  for (const card of scheduler.studiedCards(settings)) {
    const state = scheduler.state(card)
    if (!state) continue
    seen++
    if (isLearning(state)) learning++
    else if (state.state === State.Review) {
      learned++
      if (state.stability >= MASTERED_DAYS) mastered++
    }
    const due = Math.max(state.due.getTime(), today)
    if (due < horizon) {
      const dueDay = startOfStudyDay(due)
      forecast.set(dueDay, (forecast.get(dueDay) ?? 0) + 1)
    }
  }

  return {
    reviewsToday: perDay.get(today) ?? 0,
    streak,
    retention: spaced ? remembered / spaced : null,
    spacedAnswers: spaced,
    seen, learning, learned, mastered,
    perDay: [...perDay].map(([d, count]) => ({ day: d, count })),
    forecast: [...forecast].map(([d, count]) => ({ day: d, count })),
  }
}
