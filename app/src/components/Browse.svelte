<script lang="ts">
  import type { ReviewCard } from '../lib/cards'
  import { formatInterval, LEVEL_LABELS } from '../lib/format'
  import { isLearning, type Scheduler } from '../lib/scheduler'
  import type { Settings } from '../lib/settings'
  import { canSpeak, speak } from '../lib/speech'
  import type { DeckFile } from '../lib/types'

  let { deck, cards, scheduler, settings, onsuspend, onback }: {
    deck: DeckFile
    cards: ReviewCard[]
    scheduler: Scheduler
    settings: Settings
    onsuspend: (suspended: string[]) => void
    onback: () => void
  } = $props()

  const MAX_RESULTS = 50

  interface Entry {
    id: string
    kanji: string
    kana: string
    romaji: string
    french: string
    level: string | null
    kind: string
    search: string
  }

  // 'Élève' and 'eleve' match: lower case, no accents.
  const normalize = (text: string) => text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

  const entries: Entry[] = $derived([
    ...deck.decks.vocabulary.notes.map((n) => ({ ...n, kind: 'vocabulaire' })),
    ...deck.decks.conjugation.notes.map((n) => ({ ...n, kind: 'conjugaison' })),
  ].map((n) => ({
    id: n.id, kanji: n.kanji, kana: n.kana, romaji: n.romaji, french: n.french, level: n.level,
    kind: n.kind, search: normalize([n.kanji, n.kana, n.romaji, n.french].join(' ')),
  })))

  const cardsByNote = $derived.by(() => {
    const byNote = new Map<string, ReviewCard[]>()
    for (const card of cards) {
      const list = byNote.get(card.noteId) ?? []
      list.push(card)
      byNote.set(card.noteId, list)
    }
    return byNote
  })

  let query = $state('')

  const results = $derived.by(() => {
    const q = normalize(query.trim())
    if (!q) return []
    return entries.filter((e) => e.search.includes(q)).slice(0, MAX_RESULTS)
  })

  function progress(id: string): string {
    const states = (cardsByNote.get(id) ?? []).map((c) => scheduler.state(c)).filter((s) => !!s)
    if (!states.length) return 'pas encore vu'
    if (states.some(isLearning)) return 'en cours d\'apprentissage'
    const next = Math.min(...states.map((s) => s.due.getTime()))
    const delay = next - Date.now()
    return delay <= 0 ? 'à revoir aujourd\'hui' : `à revoir dans ${formatInterval(delay)}`
  }

  function toggle(id: string) {
    const suspended = settings.suspended.includes(id)
      ? settings.suspended.filter((s) => s !== id)
      : [...settings.suspended, id]
    onsuspend(suspended)
  }
</script>

<div class="browse">
  <header>
    <button class="link" onclick={onback}>‹ Accueil</button>
    <h1>Rechercher</h1>
    <span></span>
  </header>

  <!-- svelte-ignore a11y_autofocus -->
  <input type="search" bind:value={query} placeholder="kanji, kana, romaji ou français" autofocus
    autocapitalize="off" autocomplete="off" spellcheck="false" aria-label="Rechercher un mot" />

  {#if query.trim() && !results.length}
    <p class="empty">Aucun mot trouvé.</p>
  {/if}

  <ul>
    {#each results as entry (entry.id + entry.kind)}
      {@const suspended = settings.suspended.includes(entry.id)}
      <li class:suspended>
        <div class="word">
          <span class="kanji" lang="ja">{entry.kanji}</span>
          {#if entry.kana !== entry.kanji}<span class="kana" lang="ja">{entry.kana}</span>{/if}
          <span class="romaji">{entry.romaji}</span>
        </div>
        <p class="french">{entry.french}</p>
        <p class="meta">
          {entry.kind} · {LEVEL_LABELS[entry.level ?? 'none']} ·
          {suspended ? 'suspendu' : progress(entry.id)}
        </p>
        <div class="actions">
          {#if canSpeak()}
            <button class="link" onclick={() => speak(entry.kana)}>Écouter</button>
          {/if}
          <button class="link" onclick={() => toggle(entry.id)}>{suspended ? 'Réactiver' : 'Suspendre'}</button>
        </div>
      </li>
    {/each}
  </ul>
  {#if results.length === MAX_RESULTS}
    <p class="empty">Les {MAX_RESULTS} premiers résultats : précisez la recherche.</p>
  {/if}
</div>

<style>
  .browse {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 0.75rem 0 calc(2rem + env(safe-area-inset-bottom));
  }

  header {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
  }

  header .link {
    justify-self: start;
  }

  h1 {
    margin: 0;
    font-size: 1.1rem;
  }

  input {
    padding: 0.75rem 0.85rem;
    border: 1px solid var(--line);
    border-radius: 10px;
    background: var(--surface);
    color: var(--text);
    font: inherit;
    font-size: 1rem; /* 16px minimum: iOS zooms on smaller inputs */
  }

  ul {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  li {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 0.15rem 1rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--line);
  }

  li.suspended .word, li.suspended .french {
    opacity: 0.45;
  }

  .word {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.5rem;
  }

  .kanji {
    font-family: var(--font-ja);
    font-size: 1.35rem;
  }

  .kana {
    font-family: var(--font-ja);
    color: var(--kana);
  }

  .romaji {
    color: var(--muted);
    font-style: italic;
  }

  p {
    margin: 0;
  }

  .french {
    grid-column: 1;
  }

  .meta {
    grid-column: 1;
    color: var(--muted);
    font-size: 0.8rem;
  }

  .actions {
    grid-column: 2;
    grid-row: 1 / span 3;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    justify-content: center;
    gap: 0.1rem;
  }

  .actions .link {
    padding: 0.3rem 0;
    font-size: 0.9rem;
  }

  .empty {
    color: var(--muted);
    text-align: center;
  }
</style>
