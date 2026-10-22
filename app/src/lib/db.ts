// Local storage (IndexedDB): review events and settings. The deck itself is fetched from
// deck.json, which the browser (and later the service worker) caches.

import Dexie, { type EntityTable } from 'dexie'

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

export async function loadSettings(): Promise<Settings> {
  const row = await db.meta.get('settings')
  return withDefaults(row?.value as Partial<Settings> | undefined)
}

export async function saveSettings(settings: Settings): Promise<void> {
  // $state proxies can't be stored in IndexedDB: store a plain copy.
  await db.meta.put({ key: 'settings', value: JSON.parse(JSON.stringify(settings)) })
}

/** A random id for this browser, stored with each event. */
export async function deviceId(): Promise<string> {
  const row = await db.meta.get('device')
  if (row) return row.value as string
  const id = uuid()
  await db.meta.put({ key: 'device', value: id })
  return id
}
