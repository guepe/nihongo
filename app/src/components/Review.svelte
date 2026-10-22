<script lang="ts">
  import { onDestroy } from 'svelte'
  import { Rating, type Grade } from 'ts-fsrs'

  import CardFace from './CardFace.svelte'
  import type { ReviewCard } from '../lib/cards'
  import { saveEvent } from '../lib/db'
  import { formatInterval } from '../lib/format'
  import type { DeckCounts, Scheduler } from '../lib/scheduler'
  import type { Settings } from '../lib/settings'
  import { canSpeak, speak, stopSpeaking } from '../lib/speech'
  import type { DeckId } from '../lib/types'

  let { scheduler, settings, device, onexit, onsaved }: {
    scheduler: Scheduler
    settings: Settings
    device: string
    onexit: () => void
    onsaved: () => void // an event was saved locally: time to sync
  } = $props()

  const BUTTONS: { rating: Grade; label: string; key: string }[] = [
    { rating: Rating.Again, label: 'À revoir', key: '1' },
    { rating: Rating.Hard, label: 'Difficile', key: '2' },
    { rating: Rating.Good, label: 'Bien', key: '3' },
    { rating: Rating.Easy, label: 'Facile', key: '4' },
  ]

  let card = $state<ReviewCard | null>(null)
  let revealed = $state(false)
  let canUndo = $state(false)
  let counts = $state<Record<DeckId, DeckCounts>>({
    vocabulary: { learning: 0, review: 0, new: 0 },
    conjugation: { learning: 0, review: 0, new: 0 },
  })
  let waitingUntil = $state<number | null>(null)
  let now = $state(Date.now())
  let timer: ReturnType<typeof setInterval> | undefined

  const intervals = $derived.by(() => {
    if (!card || !revealed) return null
    const previewAt = Date.now()
    const dues = scheduler.preview(card, previewAt)
    return Object.fromEntries(BUTTONS.map((b) => [b.rating, formatInterval(dues[b.rating].getTime() - previewAt)]))
  })

  function japaneseOf(c: ReviewCard): string {
    return c.deck === 'vocabulary' ? c.note.kana : c.form.kana
  }

  function speakCard() {
    if (card) speak(japaneseOf(card))
  }

  // Called from a tap or a key press, so that iOS allows the speech.
  function reveal() {
    if (!card || revealed) return
    revealed = true
    if (settings.autoplay) speakCard()
  }

  function showNext() {
    stopSpeaking()
    const at = Date.now()
    card = scheduler.next(settings, at)
    revealed = false
    counts = scheduler.counts(settings, at)
    waitingUntil = card ? null : scheduler.nextLearningDue(settings, at)
    clearInterval(timer)
    if (waitingUntil !== null) {
      // A learning card comes back in a few minutes: wait for it.
      timer = setInterval(() => {
        now = Date.now()
        if (waitingUntil !== null && now >= waitingUntil) showNext()
      }, 1000)
    }
  }

  async function answer(rating: Grade) {
    if (!card || !revealed) return
    const event = scheduler.answer(card, rating, Date.now(), device)
    canUndo = true
    showNext()
    await saveEvent(event)
    onsaved()
  }

  async function undo() {
    const result = scheduler.undo(Date.now(), device)
    if (!result) return
    card = result.card
    revealed = false
    counts = scheduler.counts(settings, Date.now())
    waitingUntil = null
    clearInterval(timer)
    canUndo = false
    await saveEvent(result.event)
    onsaved()
  }

  function onkeydown(event: KeyboardEvent) {
    if (event.metaKey || event.ctrlKey || event.altKey) {
      if (event.key === 'z' && canUndo) {
        event.preventDefault()
        undo()
      }
      return
    }
    if (!card) return
    if (!revealed && (event.key === ' ' || event.key === 'Enter')) {
      event.preventDefault()
      reveal()
    } else if (revealed) {
      if (event.key === 'r') {
        speakCard()
        return
      }
      const button = BUTTONS.find((b) => b.key === event.key)
      if (button) answer(button.rating)
      else if (event.key === ' ' || event.key === 'Enter') {
        event.preventDefault()
        answer(Rating.Good)
      }
    }
  }

  showNext()
  onDestroy(() => {
    clearInterval(timer)
    stopSpeaking()
  })
</script>

<svelte:window {onkeydown} />

<div class="review">
  <header>
    <button class="link" onclick={onexit}>‹ Accueil</button>
    <div class="counts" aria-label="Cartes restantes">
      <span class="new" title="Nouvelles">{counts.vocabulary.new + counts.conjugation.new}</span>
      <span class="learning" title="En cours d'apprentissage">{counts.vocabulary.learning + counts.conjugation.learning}</span>
      <span class="due" title="À réviser">{counts.vocabulary.review + counts.conjugation.review}</span>
    </div>
    <button class="link" onclick={undo} disabled={!canUndo} title="Annuler la dernière réponse (⌘Z)">Annuler</button>
  </header>

  {#if card}
    <!-- Tapping the card shows the answer, like the button. -->
    <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
    <main class="card" onclick={reveal}>
      {#key card.key}
        <CardFace {card} {revealed} showFurigana={settings.furigana}
          onspeak={canSpeak() ? speakCard : undefined} />
      {/key}
    </main>

    <nav class="actions">
      {#if !revealed}
        <button class="reveal" onclick={reveal}>Montrer la réponse</button>
      {:else}
        {#each BUTTONS as button (button.rating)}
          <button class="grade grade-{button.rating}" onclick={() => answer(button.rating)}>
            <span class="interval">{intervals?.[button.rating]}</span>
            {button.label}
          </button>
        {/each}
      {/if}
    </nav>
  {:else}
    <main class="done">
      {#if waitingUntil !== null}
        <p class="big">Petite pause…</p>
        <p>Une carte en cours d'apprentissage revient dans {formatInterval(Math.max(0, waitingUntil - now))}.</p>
      {:else}
        <p class="big" lang="ja">おつかれさま！</p>
        <p>C'est terminé pour aujourd'hui.</p>
      {/if}
      <button class="primary" onclick={onexit}>Retour à l'accueil</button>
    </main>
  {/if}
</div>

<style>
  .review {
    display: flex;
    flex-direction: column;
    min-height: 100dvh;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0;
  }

  .counts {
    display: flex;
    gap: 0.9rem;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
  }

  .counts .new { color: var(--new); }
  .counts .learning { color: var(--again); }
  .counts .due { color: var(--good); }

  .card {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 1.5rem 0;
    cursor: default;
  }

  .actions {
    position: sticky;
    bottom: 0;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
    padding: 0.75rem 0 calc(0.75rem + env(safe-area-inset-bottom));
    background: var(--bg);
  }

  .reveal {
    grid-column: 1 / -1;
  }

  .actions button {
    min-height: 3.5rem;
    border-radius: 12px;
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--text);
    font-size: 1rem;
  }

  .grade {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.1rem;
    font-weight: 600;
  }

  .interval {
    font-size: 0.75rem;
    font-weight: 400;
    color: var(--muted);
  }

  .grade-1 { color: var(--again) !important; }
  .grade-2 { color: var(--hard) !important; }
  .grade-3 { color: var(--good) !important; }
  .grade-4 { color: var(--easy) !important; }

  .done {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    text-align: center;
  }

  .big {
    font-size: 2rem;
    margin: 0;
  }
</style>
