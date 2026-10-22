// Synchronisation with the server: local review events are sent, the other devices' events
// are fetched (see the event log in scheduler.ts), and the most recent settings win.

import { api, type Session } from './api'
import { db, getMeta, loadSettings, saveSettings, setMeta, type StoredEvent } from './db'
import type { ReviewEvent } from './scheduler'
import { withDefaults, type Settings } from './settings'

const BATCH = 500

/** What the account screen shows. */
export interface SyncStatus {
  syncing: boolean
  pending: number // local events not sent yet
  error: string | null
}

export interface SyncResult {
  /** Events from other devices, new on this one: the scheduler must be rebuilt. */
  pulled: number
  /** The server had more recent settings, now saved locally. */
  settingsChanged: boolean
}

export async function pendingCount(): Promise<number> {
  return db.events.where('synced').equals(0).count()
}

async function push(token: string) {
  for (;;) {
    const pending = await db.events.where('synced').equals(0).limit(BATCH).toArray()
    if (!pending.length) return
    const events: ReviewEvent[] = pending.map(({ synced: _, ...event }) => event)
    await api('POST', 'events', { events }, token)
    await db.events.bulkUpdate(pending.map((e) => ({ key: e.id, changes: { synced: 1 as const } })))
  }
}

async function pull(token: string): Promise<number> {
  let since = (await getMeta<number>('lastSeq')) ?? 0
  let added = 0
  for (;;) {
    const page = await api<{ events: ReviewEvent[]; last: number; more: boolean }>(
      'GET', `events?since=${since}`, undefined, token)
    const known = await db.events.bulkGet(page.events.map((e) => e.id))
    const fresh: StoredEvent[] = page.events
      .filter((_, i) => !known[i])
      .map((e) => ({ ...e, synced: 1 }))
    await db.events.bulkPut(fresh)
    added += fresh.length
    since = page.last
    await setMeta('lastSeq', since)
    if (!page.more) return added
  }
}

async function syncSettings(token: string): Promise<boolean> {
  const localAt = (await getMeta<number>('settingsUpdatedAt')) ?? 0
  const remote = await api<{ settings: Partial<Settings> | null; updated_at: number }>(
    'GET', 'settings', undefined, token)
  if (remote.settings && remote.updated_at > localAt) {
    await saveSettings(withDefaults(remote.settings), remote.updated_at)
    return true
  }
  if (localAt > remote.updated_at || !remote.settings) {
    const updatedAt = localAt || Date.now()
    await api('PUT', 'settings', { settings: await loadSettings(), updated_at: updatedAt }, token)
    if (!localAt) await setMeta('settingsUpdatedAt', updatedAt)
  }
  return false
}

let running: Promise<SyncResult> | null = null
let again = false

/** Runs one synchronisation at a time; a call during a run schedules one more run. */
export function sync(session: Session): Promise<SyncResult> {
  if (running) {
    again = true
    return running
  }
  running = (async () => {
    const total: SyncResult = { pulled: 0, settingsChanged: false }
    try {
      do {
        again = false
        await push(session.token)
        total.pulled += await pull(session.token)
        total.settingsChanged ||= await syncSettings(session.token)
      } while (again)
      return total
    } finally {
      running = null
    }
  })()
  return running
}
