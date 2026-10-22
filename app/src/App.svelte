<script lang="ts">
  import Home from './components/Home.svelte'
  import Review from './components/Review.svelte'
  import SettingsForm from './components/SettingsForm.svelte'
  import { buildCards, type ReviewCard } from './lib/cards'
  import { deviceId, loadEvents, loadSettings, saveSettings } from './lib/db'
  import { Scheduler } from './lib/scheduler'
  import type { Settings } from './lib/settings'
  import { DECK_FORMAT, type DeckFile } from './lib/types'

  type Screen = 'home' | 'review' | 'settings'

  let screen = $state<Screen>('home')
  let deck = $state.raw<DeckFile | null>(null)
  let cards: ReviewCard[] = []
  let scheduler = $state.raw<Scheduler | null>(null)
  let settings = $state<Settings | null>(null)
  let device = $state('')
  let error = $state<string | null>(null)
  // Recomputed when coming back to the home screen.
  let refresh = $state(0)

  const counts = $derived.by(() => {
    void refresh
    return scheduler && settings ? scheduler.counts(settings, Date.now()) : null
  })

  async function start() {
    try {
      const response = await fetch(import.meta.env.BASE_URL + 'deck.json')
      if (!response.ok) throw new Error(`deck.json : erreur ${response.status}`)
      const file: DeckFile = await response.json()
      if (file.format !== DECK_FORMAT) throw new Error(`deck.json : format ${file.format} inconnu`)
      deck = file
      cards = buildCards(file)
      settings = await loadSettings()
      device = await deviceId()
      scheduler = new Scheduler(cards, await loadEvents(), settings.retention)
    } catch (e) {
      error = e instanceof Error ? e.message : String(e)
    }
  }

  async function save(next: Settings) {
    const retentionChanged = next.retention !== settings!.retention
    settings = next
    await saveSettings(next)
    // Intervals depend on the retention: recompute every card from its history.
    if (retentionChanged) scheduler = new Scheduler(cards, await loadEvents(), next.retention)
    goHome()
  }

  function goHome() {
    refresh++
    screen = 'home'
  }

  start()
</script>

<div class="page">
  {#if error}
    <p class="message">Impossible de charger les cartes. {error}</p>
  {:else if !scheduler || !settings || !deck || !counts}
    <p class="message">Chargement…</p>
  {:else if screen === 'review'}
    <Review {scheduler} {settings} {device} onexit={goHome} />
  {:else if screen === 'settings'}
    <SettingsForm {settings} conjugations={deck.decks.conjugation.conjugations}
      onsave={save} oncancel={() => (screen = 'home')} />
  {:else}
    <Home {counts} {settings} onstart={() => (screen = 'review')} onsettings={() => (screen = 'settings')} />
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
