<script lang="ts">
  import { untrack } from 'svelte'

  import { LEVELS, NO_LEVEL } from '../lib/cards'
  import { LEVEL_LABELS } from '../lib/format'
  import type { Settings } from '../lib/settings'
  import type { Conjugation, DeckId } from '../lib/types'

  let { settings, conjugations, onsave, oncancel }: {
    settings: Settings
    conjugations: Conjugation[]
    onsave: (settings: Settings) => void
    oncancel: () => void
  } = $props()

  // Edit a copy: nothing changes until "Enregistrer".
  let draft = $state(untrack(() => $state.snapshot(settings)))

  const DECKS: { id: DeckId; label: string }[] = [
    { id: 'vocabulary', label: 'Vocabulaire' },
    { id: 'conjugation', label: 'Conjugaison' },
  ]
  const levels = [...LEVELS, NO_LEVEL]

  function toggle(list: string[], value: string) {
    const index = list.indexOf(value)
    if (index === -1) list.push(value)
    else list.splice(index, 1)
  }
</script>

<div class="settings">
  <header>
    <button class="link" onclick={oncancel}>‹ Annuler</button>
    <h1>Réglages</h1>
    <button class="link strong" onclick={() => onsave($state.snapshot(draft))}>Enregistrer</button>
  </header>

  <section>
    <h2>Decks</h2>
    {#each DECKS as deck (deck.id)}
      <div class="row">
        <label class="check">
          <input type="checkbox" bind:checked={draft.decks[deck.id].enabled} />
          {deck.label}
        </label>
        <label class="number">
          <input type="number" min="0" max="200" inputmode="numeric"
            bind:value={draft.decks[deck.id].newPerDay} disabled={!draft.decks[deck.id].enabled} />
          nouvelles / jour
        </label>
      </div>
    {/each}
  </section>

  <section>
    <h2>Niveaux JLPT</h2>
    <div class="chips">
      {#each levels as level (level)}
        <label class="chip">
          <input type="checkbox" checked={draft.levels.includes(level)} onchange={() => toggle(draft.levels, level)} />
          {LEVEL_LABELS[level]}
        </label>
      {/each}
    </div>
  </section>

  <section>
    <h2>Formes de conjugaison</h2>
    <p class="hint">
      Chaque forme ajoute de 4 à 8 cartes par verbe. Commencez par quelques-unes, et ajoutez
      les autres au fil du temps.
    </p>
    <div class="chips">
      {#each conjugations as conjugation (conjugation.id)}
        <label class="chip">
          <input type="checkbox" checked={draft.conjugations.includes(conjugation.id)}
            onchange={() => toggle(draft.conjugations, conjugation.id)} />
          {conjugation.label}
        </label>
      {/each}
    </div>
  </section>

  <section>
    <h2>Affichage et son</h2>
    <div class="row">
      <label class="check">
        <input type="checkbox" bind:checked={draft.furigana} />
        Furigana au-dessus des kanji
      </label>
    </div>
    <div class="row">
      <label class="check">
        <input type="checkbox" bind:checked={draft.autoplay} />
        Lire le japonais en montrant la réponse
      </label>
    </div>
    <p class="hint">Le bouton haut-parleur (ou la touche R) relit le mot à tout moment.</p>
  </section>

  <section>
    <h2>Rétention visée</h2>
    <label class="range">
      <input type="range" min="0.75" max="0.97" step="0.01" bind:value={draft.retention} />
      <span>{Math.round(draft.retention * 100)} %</span>
    </label>
    <p class="hint">
      La part des cartes dont vous vous souvenez au moment de les revoir. Plus elle est
      haute, plus les révisions sont fréquentes. 90 % est un bon équilibre.
    </p>
  </section>
</div>

<style>
  .settings {
    display: flex;
    flex-direction: column;
    gap: 1.75rem;
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

  header .strong {
    justify-self: end;
    font-weight: 600;
  }

  h1 {
    margin: 0;
    font-size: 1.1rem;
  }

  h2 {
    margin: 0 0 0.75rem;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
  }

  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--line);
  }

  label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .number {
    color: var(--muted);
    font-size: 0.9rem;
  }

  .number input {
    width: 4.5rem;
    padding: 0.4rem 0.5rem;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface);
    color: var(--text);
    font-size: 1rem;
    text-align: right;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .chip {
    padding: 0.45rem 0.8rem;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: var(--surface);
    font-size: 0.95rem;
    cursor: pointer;
  }

  .chip:has(input:checked) {
    border-color: var(--accent);
    color: var(--accent);
  }

  .chip input {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  .chip:has(input:focus-visible) {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }

  .range input {
    flex: 1;
    accent-color: var(--accent);
  }

  .range span {
    width: 3.5rem;
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .hint {
    margin: 0.5rem 0 0.75rem;
    color: var(--muted);
    font-size: 0.85rem;
  }
</style>
