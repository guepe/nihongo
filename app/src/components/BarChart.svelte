<script lang="ts">
  // Bars of a single series: one bar per day, value on hover (or tap), table for screen readers.

  let { data, label }: {
    data: { label: string; short: string; value: number }[]
    label: string // what the values count, eg. "révisions"
  } = $props()

  let active = $state<number | null>(null)

  const max = $derived(Math.max(1, ...data.map((d) => d.value)))
  // A rounded scale top: 5, 10, 20, 50, 100…
  const top = $derived.by(() => {
    const step = 10 ** Math.floor(Math.log10(max))
    return [1, 2, 5, 10].map((m) => m * step).find((v) => v >= max) ?? max
  })
</script>

<figure>
  <div class="plot" role="img" aria-label="{label} par jour (détail dans le tableau)">
    <div class="scale" aria-hidden="true"><span>{top}</span><span>0</span></div>
    <div class="bars" aria-hidden="true" onpointerleave={() => (active = null)}>
      {#each data as d, i (i)}
        <!-- The whole column reacts, not only the bar: easier to hit, even for a zero. -->
        <div class="column" role="presentation" onpointerenter={() => (active = i)} onpointerdown={() => (active = i)}>
          {#if d.value > 0}
            <div class="bar" class:active={active === i} style:height="{(d.value / top) * 100}%"></div>
          {/if}
        </div>
      {/each}
    </div>
    {#if active !== null}
      {@const position = (active + 0.5) / data.length}
      <!-- Near the edges, the tooltip is aligned with the bar instead of centred on it. -->
      <div class="tooltip" style:left="calc(2rem + (100% - 2rem) * {position})"
        style:transform="translateX({position < 0.2 ? -10 : position > 0.8 ? -90 : -50}%)">
        <strong>{data[active].value}</strong> {label}<br /><span>{data[active].label}</span>
      </div>
    {/if}
  </div>
  <div class="axis" aria-hidden="true">
    <span>{data[0]?.short}</span>
    <span>{data[Math.floor(data.length / 2)]?.short}</span>
    <span>{data[data.length - 1]?.short}</span>
  </div>

  <details>
    <summary>Voir les chiffres</summary>
    <table>
      <tbody>
        {#each data as d, i (i)}
          <tr><th scope="row">{d.label}</th><td>{d.value}</td></tr>
        {/each}
      </tbody>
    </table>
  </details>
</figure>

<style>
  figure {
    margin: 0;
  }

  .plot {
    position: relative;
    padding-left: 2rem;
  }

  .scale {
    position: absolute;
    left: 0;
    top: -0.5em;
    bottom: -0.5em;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    color: var(--muted);
    font-size: 0.7rem;
    font-variant-numeric: tabular-nums;
  }

  .bars {
    display: flex;
    align-items: stretch;
    gap: 2px;
    height: 120px;
    border-bottom: 1px solid var(--muted);
    background:
      linear-gradient(var(--line), var(--line)) 0 0 / 100% 1px no-repeat,
      linear-gradient(var(--line), var(--line)) 0 50% / 100% 1px no-repeat;
  }

  .column {
    flex: 1;
    display: flex;
    align-items: flex-end;
    min-width: 0;
  }

  .bar {
    width: 100%;
    min-height: 2px;
    border-radius: 4px 4px 0 0;
    background: var(--bar);
  }

  .bar.active {
    background: var(--text);
  }

  .tooltip {
    position: absolute;
    bottom: calc(100% + 0.25rem);
    padding: 0.35rem 0.6rem;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface);
    box-shadow: 0 4px 14px rgb(0 0 0 / 0.12);
    font-size: 0.8rem;
    white-space: nowrap;
    pointer-events: none;
  }

  .tooltip span {
    color: var(--muted);
  }

  .axis {
    display: flex;
    justify-content: space-between;
    padding: 0.3rem 0 0 2rem;
    color: var(--muted);
    font-size: 0.7rem;
  }

  details {
    margin-top: 0.5rem;
    font-size: 0.8rem;
    color: var(--muted);
  }

  summary {
    cursor: pointer;
  }

  table {
    width: 100%;
    margin-top: 0.4rem;
    border-collapse: collapse;
    font-variant-numeric: tabular-nums;
  }

  th, td {
    padding: 0.15rem 0;
    font-weight: 400;
    text-align: left;
  }

  td {
    text-align: right;
    color: var(--text);
  }
</style>
