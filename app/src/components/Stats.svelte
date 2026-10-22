<script lang="ts">
  import BarChart from './BarChart.svelte'
  import type { Scheduler } from '../lib/scheduler'
  import type { Settings } from '../lib/settings'
  import { computeStats, type DayCount } from '../lib/stats'

  let { scheduler, settings, onback }: {
    scheduler: Scheduler
    settings: Settings
    onback: () => void
  } = $props()

  const stats = $derived(computeStats(scheduler, settings, Date.now()))

  const long = (day: number) =>
    new Date(day).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })
  const short = (day: number) =>
    new Date(day).toLocaleDateString('fr-FR', { day: 'numeric', month: 'numeric' })
  const bars = (days: DayCount[], first?: string) =>
    days.map((d, i) => ({
      label: i === 0 && first ? first : long(d.day),
      short: i === 0 && first ? first : short(d.day),
      value: d.count,
    }))
  const percent = (n: number) => `${Math.round(n * 100)} %`
</script>

<div class="stats">
  <header>
    <button class="link" onclick={onback}>‹ Accueil</button>
    <h1>Statistiques</h1>
    <span></span>
  </header>

  <div class="tiles">
    <div class="tile">
      <span class="value">{stats.streak}</span>
      <span class="name">jour{stats.streak > 1 ? 's' : ''} d'affilée</span>
    </div>
    <div class="tile">
      <span class="value">{stats.reviewsToday}</span>
      <span class="name">révision{stats.reviewsToday > 1 ? 's' : ''} aujourd'hui</span>
    </div>
    <div class="tile">
      <span class="value">{stats.retention === null ? '–' : percent(stats.retention)}</span>
      <span class="name">de réussite sur 30 jours</span>
    </div>
    <div class="tile">
      <span class="value">{stats.learned}</span>
      <span class="name">carte{stats.learned > 1 ? 's' : ''} apprise{stats.learned > 1 ? 's' : ''}</span>
    </div>
  </div>
  {#if stats.retention === null}
    <p class="hint">La réussite se calcule sur les cartes revues au moins un jour après la précédente révision.</p>
  {:else}
    <p class="hint">
      Sur {stats.spacedAnswers} révision{stats.spacedAnswers > 1 ? 's' : ''} espacée{stats.spacedAnswers > 1 ? 's' : ''},
      rétention visée : {percent(settings.retention)}.
    </p>
  {/if}

  <section>
    <h2>Révisions des 30 derniers jours</h2>
    <BarChart data={bars(stats.perDay)} label="révisions" />
  </section>

  <section>
    <h2>Cartes à revoir dans les 14 jours</h2>
    <BarChart data={bars(stats.forecast, 'auj.')} label="cartes à revoir" />
  </section>

  <section>
    <h2>Cartes vues</h2>
    <dl>
      <dt>En cours d'apprentissage</dt><dd>{stats.learning}</dd>
      <dt>Apprises</dt><dd>{stats.learned}</dd>
      <dt>Maîtrisées (mémoire de 3 semaines ou plus)</dt><dd>{stats.mastered}</dd>
      <dt>Total</dt><dd>{stats.seen}</dd>
    </dl>
  </section>
</div>

<style>
  .stats {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
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

  h2 {
    margin: 0 0 1rem;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
  }

  .tiles {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.6rem;
  }

  .tile {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    padding: 0.85rem 1rem;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--surface);
  }

  .value {
    font-size: 1.8rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
  }

  .name {
    color: var(--muted);
    font-size: 0.85rem;
  }

  .hint {
    margin: -0.75rem 0 0;
    color: var(--muted);
    font-size: 0.8rem;
  }

  dl {
    display: grid;
    grid-template-columns: 1fr auto;
    margin: 0;
  }

  dt, dd {
    margin: 0;
    padding: 0.55rem 0;
    border-bottom: 1px solid var(--line);
  }

  dd {
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    text-align: right;
  }
</style>
