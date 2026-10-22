<script lang="ts">
  import type { DeckCounts } from '../lib/scheduler'
  import type { Settings } from '../lib/settings'
  import type { SyncStatus } from '../lib/sync'
  import type { DeckId } from '../lib/types'

  let { counts, settings, status, onstart, onsettings, onstats, onbrowse }: {
    counts: Record<DeckId, DeckCounts>
    settings: Settings
    status: SyncStatus
    onstart: () => void
    onsettings: () => void
    onstats: () => void
    onbrowse: () => void
  } = $props()

  const DECKS: { id: DeckId; label: string }[] = [
    { id: 'vocabulary', label: 'Vocabulaire' },
    { id: 'conjugation', label: 'Conjugaison' },
  ]

  const total = $derived(DECKS.reduce((sum, d) =>
    sum + (settings.decks[d.id].enabled ? counts[d.id].new + counts[d.id].learning + counts[d.id].review : 0), 0))
</script>

<div class="home">
  <header>
    <h1><span lang="ja">蜂</span> hachi</h1>
    <button class="link" onclick={onsettings}>Réglages</button>
  </header>

  <table>
    <thead>
      <tr>
        <th></th>
        <th class="new">Nouvelles</th>
        <th class="learning">En cours</th>
        <th class="due">À réviser</th>
      </tr>
    </thead>
    <tbody>
      {#each DECKS as deck (deck.id)}
        <tr class:disabled={!settings.decks[deck.id].enabled}>
          <th scope="row">{deck.label}</th>
          {#if settings.decks[deck.id].enabled}
            <td class="new">{counts[deck.id].new}</td>
            <td class="learning">{counts[deck.id].learning}</td>
            <td class="due">{counts[deck.id].review}</td>
          {:else}
            <td colspan="3">désactivé</td>
          {/if}
        </tr>
      {/each}
    </tbody>
  </table>

  {#if total > 0}
    <button class="primary start" onclick={onstart}>Commencer</button>
  {:else}
    <p class="rest"><span lang="ja">おつかれさま！</span> Rien à réviser pour aujourd'hui.</p>
  {/if}

  <nav>
    <button onclick={onstats}>Statistiques</button>
    <button onclick={onbrowse}>Rechercher un mot</button>
  </nav>

  <p class="sync" class:warning={status.pending > 0 && !status.syncing}>
    {#if status.syncing}
      Synchronisation…
    {:else if status.pending}
      {status.pending} révision{status.pending > 1 ? 's' : ''} à envoyer{status.error ? ` (${status.error.toLowerCase()})` : ''}
    {:else if status.error}
      {status.error}
    {:else}
      Synchronisé
    {/if}
  </p>
</div>

<style>
  .home {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    padding: 1rem 0 calc(2rem + env(safe-area-inset-bottom));
  }

  header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
  }

  h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  h1 span {
    font-family: var(--font-ja);
    color: var(--accent);
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-variant-numeric: tabular-nums;
  }

  th, td {
    padding: 0.85rem 0.25rem;
    border-bottom: 1px solid var(--line);
    text-align: right;
  }

  thead th {
    font-size: 0.8rem;
    font-weight: 500;
  }

  tbody th {
    text-align: left;
    font-weight: 600;
  }

  td {
    font-size: 1.25rem;
    font-weight: 600;
  }

  .new { color: var(--new); }
  .learning { color: var(--again); }
  .due { color: var(--good); }

  tr.disabled td {
    color: var(--muted);
    font-size: 0.9rem;
    font-weight: 400;
  }

  .start {
    min-height: 3.5rem;
    font-size: 1.1rem;
  }

  nav {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
    margin-top: -0.75rem;
  }

  nav button {
    padding: 0.75rem;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--surface);
    color: var(--text);
  }

  .sync {
    margin: 0;
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
  }

  .sync.warning {
    color: var(--hard);
  }

  .rest {
    text-align: center;
    color: var(--muted);
  }
</style>
