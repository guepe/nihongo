// Local storage (IndexedDB): review events and settings. The deck itself is fetched from
// deck.json, which the browser (and later the service worker) caches.

import Dexie, { type EntityTable } from 'dexie'

import type { Session } from './api'
import type { ReviewEvent } from './scheduler'
import { withDefaults, type Settings } from './settings'
import { uuid } from './scheduler'

export interface StoredEvent extends ReviewEvent {
  synced: 0 | 1 // sent to the server (phase D); IndexedDB can't index booleans
}

interface KeyValue {
  key: string
  value: unknown
}

class HachiDatabase extends Dexie {
  events!: EntityTable<StoredEvent, 'id'>
  meta!: EntityTable<KeyValue, 'key'>

  constructor() {
    super('hachi')
    this.version(1).stores({
      events: 'id, at, synced',
      meta: 'key',
    })
  }
}

export const db = new HachiDatabase()

export async function loadEvents(): Promise<ReviewEvent[]> {
  return db.events.toArray()
}

export async function saveEvent(event: ReviewEvent): Promise<void> {
  await db.events.put({ ...event, synced: 0 })
}

export async function getMeta<T>(key: string): Promise<T | undefined> {
  return (await db.meta.get(key))?.value as T | undefined
}

export async function setMeta(key: string, value: unknown): Promise<void> {
  await db.meta.put({ key, value })
}

export async function loadSettings(): Promise<Settings> {
  return withDefaults(await getMeta<Partial<Settings>>('settings'))
}

/** updatedAt decides which device's settings win when syncing (the most recent). */
export async function saveSettings(settings: Settings, updatedAt = Date.now()): Promise<void> {
  // $state proxies can't be stored in IndexedDB: store a plain copy.
  await setMeta('settings', JSON.parse(JSON.stringify(settings)))
  await setMeta('settingsUpdatedAt', updatedAt)
}

export async function loadSession(): Promise<Session | undefined> {
  return getMeta<Session>('session')
}

export async function saveSession(session: Session): Promise<void> {
  await setMeta('session', session)
}

export async function clearSession(): Promise<void> {
  await db.meta.delete('session')
}

/** After logging out: the next account on this device starts from a clean slate. */
export async function clearAccountData(): Promise<void> {
  await db.transaction('rw', db.events, db.meta, async () => {
    await db.events.clear()
    await db.meta.bulkDelete(['session', 'settings', 'settingsUpdatedAt', 'lastSeq'])
  })
}

/** A random id for this browser, stored with each event. */
export async function deviceId(): Promise<string> {
  const row = await db.meta.get('device')
  if (row) return row.value as string
  const id = uuid()
  await db.meta.put({ key: 'device', value: id })
  return id
}
