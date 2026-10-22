<script lang="ts">
  import Account from './components/Account.svelte'
  import Browse from './components/Browse.svelte'
  import Home from './components/Home.svelte'
  import Login from './components/Login.svelte'
  import Review from './components/Review.svelte'
  import SettingsForm from './components/SettingsForm.svelte'
  import Stats from './components/Stats.svelte'
  import UpdateBanner from './components/UpdateBanner.svelte'
  import { ApiError, type Session } from './lib/api'
  import { buildCards, type ReviewCard } from './lib/cards'
  import {
    clearAccountData, clearSession, deviceId, loadEvents, loadSession, loadSettings, saveSession,
    saveSettings,
  } from './lib/db'
  import { Scheduler } from './lib/scheduler'
  import type { Settings } from './lib/settings'
  import { pendingCount, sync, type SyncStatus } from './lib/sync'
  import { DECK_FORMAT, type DeckFile } from './lib/types'

  type Screen = 'home' | 'review' | 'settings' | 'stats' | 'browse'

  const SYNC_DELAY = 3000 // after an answer, wait for the next ones before sending
  const SYNC_EVERY = 5 * 60 * 1000

  let screen = $state<Screen>('home')
  let deck = $state.raw<DeckFile | null>(null)
  let cards = $state.raw<ReviewCard[]>([])
  let scheduler = $state.raw<Scheduler | null>(null)
  let settings = $state<Settings | null>(null)
  let session = $state.raw<Session | null>(null)
  let device = $state('')
  let ready = $state(false)
  let error = $state<string | null>(null)
  let status = $state<SyncStatus>({ syncing: false, pending: 0, error: null })
  // Recomputed when coming back to the home screen.
  let refresh = $state(0)
  // Events from other devices arrived during a review: rebuild once back home.
  let stale = false
  let syncTimer: ReturnType<typeof setTimeout> | undefined

  const counts = $derived.by(() => {
    void refresh
    return scheduler && settings ? scheduler.counts(settings, Date.now()) : null
  })

  async function start() {
    // Without this, Safari may clear IndexedDB (the whole progress) of a site unused for a
    // few weeks. Apps added to the home screen are already exempt.
    navigator.storage?.persist?.()
    try {
      const response = await fetch(import.meta.env.BASE_URL + 'deck.json')
      if (!response.ok) throw new Error(`deck.json : erreur ${response.status}`)
      const file: DeckFile = await response.json()
      if (file.format !== DECK_FORMAT) throw new Error(`deck.json : format ${file.format} inconnu`)
      deck = file
      cards = buildCards(file)
      device = await deviceId()
      session = (await loadSession()) ?? null
      await rebuild()
      ready = true
      if (session) runSync()
    } catch (e) {
      error = e instanceof Error ? e.message : String(e)
    }
  }

  async function rebuild() {
    settings = await loadSettings()
    scheduler = new Scheduler(cards, await loadEvents(), settings.retention)
    stale = false
    refresh++
  }

  async function runSync() {
    if (!session) return
    clearTimeout(syncTimer)
    status.syncing = true
    try {
      const result = await sync(session)
      status.error = null
      if (result.pulled || result.settingsChanged) {
        if (screen === 'home') await rebuild()
        else stale = true
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        // Session closed elsewhere: log in again. Local reviews are kept and sent afterwards.
        session = null
        await clearSession()
      }
      status.error = e instanceof ApiError && e.status === 0
        ? 'Hors ligne'
        : e instanceof Error ? e.message : String(e)
    } finally {
      status.syncing = false
      status.pending = await pendingCount()
    }
  }

  function scheduleSync() {
    clearTimeout(syncTimer)
    syncTimer = setTimeout(runSync, SYNC_DELAY)
  }

  async function login(next: Session) {
    screen = 'home'
    session = next
    await saveSession(next)
    // Reviews made on this device before logging in are sent to the account, and those of
    // the other devices arrive (the scheduler is rebuilt if the home screen is shown).
    await runSync()
  }

  async function logout() {
    await runSync()
    if (status.pending > 0) {
      const lose = confirm(`${status.pending} révision(s) n'ont pas pu être envoyées et seront perdues. Se déconnecter quand même ?`)
      if (!lose) return
    }
    try {
      await fetch('/api/logout', { method: 'POST', headers: { 'X-Hachi-Token': session!.token } })
    } catch {
      // Offline: the session will expire on the server, nothing else to do.
    }
    await clearAccountData()
    session = null
    status = { syncing: false, pending: 0, error: null }
    await rebuild()
    screen = 'home'
  }

  async function save(next: Settings) {
    await saveSettings(next)
    await rebuild()
    screen = 'home'
    scheduleSync()
  }

  async function suspend(suspended: string[]) {
    const next = { ...$state.snapshot(settings!), suspended }
    settings = next
    await saveSettings(next)
    scheduleSync()
  }

  async function goHome() {
    if (stale) await rebuild()
    else refresh++
    screen = 'home'
    runSync()
  }

  function onvisibilitychange() {
    if (document.visibilityState === 'visible' && screen === 'home') runSync()
  }

  setInterval(() => {
    if (document.visibilityState === 'visible') runSync()
  }, SYNC_EVERY)

  start()
</script>

<svelte:window ononline={runSync} />
<svelte:document {onvisibilitychange} />

<UpdateBanner />

<div class="page">
  {#if error}
    <p class="message">Impossible de charger les cartes. {error}</p>
  {:else if !ready || !scheduler || !settings || !deck || !counts}
    <p class="message">Chargement…</p>
  {:else if !session}
    <Login {device} onlogin={login} />
  {:else if screen === 'review'}
    <Review {scheduler} {settings} {device} onexit={goHome} onsaved={scheduleSync} />
  {:else if screen === 'settings'}
    <SettingsForm {settings} conjugations={deck.decks.conjugation.conjugations}
      onsave={save} oncancel={() => (screen = 'home')} />
    <Account {session} {status} onsync={runSync} onlogout={logout} />
  {:else if screen === 'stats'}
    <Stats {scheduler} {settings} onback={goHome} />
  {:else if screen === 'browse'}
    <Browse {deck} {cards} {scheduler} {settings} onsuspend={suspend} onback={goHome} />
  {:else}
    <Home {counts} {settings} {status} onstart={() => (screen = 'review')}
      onsettings={() => (screen = 'settings')} onstats={() => (screen = 'stats')}
      onbrowse={() => (screen = 'browse')} />
  {/if}
</div>

<style>
  .page {
    max-width: 34rem;
    margin: 0 auto;
    padding: 0 1rem;
    padding-top: env(safe-area-inset-top);
  }

  .message {
    margin-top: 40vh;
    text-align: center;
    color: var(--muted);
  }
</style>
