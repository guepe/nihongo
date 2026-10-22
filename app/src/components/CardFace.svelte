<script lang="ts">
  import type { ReviewCard } from '../lib/cards'
  import { LEVEL_LABELS } from '../lib/format'

  let { card, revealed }: { card: ReviewCard; revealed: boolean } = $props()

  const GROUPS: Record<string, string> = {
    ichidan: 'ichidan (ru)', irregular: 'irrégulier', 'suru-verb': 'verbe en する',
    'godan-aru-special': 'godan (spécial, ある)',
  }
  const groupLabel = (group: string) =>
    GROUPS[group] ?? group.replace(/^godan-(.+)$/, 'godan ($1)')
</script>

{#if card.deck === 'vocabulary'}
  {@const note = card.note}
  {@const kanaDiffers = note.kana !== note.kanji}
  <div class="face">
    {#if card.type === 'fr-jp'}
      <p class="french question">{note.french}</p>
    {:else if card.type === 'furigana'}
      <p class="japanese question" lang="ja">{note.kanji}</p>
      {#if kanaDiffers}<p class="kana" lang="ja">{note.kana}</p>{/if}
    {:else if card.type === 'kanji'}
      <p class="japanese question" lang="ja">{note.kanji}</p>
    {:else}
      <p class="japanese question" lang="ja">{note.kana}</p>
    {/if}

    {#if revealed}
      <hr />
      {#if card.type === 'fr-jp'}
        <p class="japanese" lang="ja">{note.kanji}</p>
        {#if kanaDiffers}<p class="kana" lang="ja">{note.kana}</p>{/if}
        <p class="romaji">{note.romaji}</p>
      {:else if card.type === 'furigana'}
        <p class="romaji">{note.romaji}</p>
        <p class="french">{note.french}</p>
      {:else if card.type === 'kanji'}
        {#if kanaDiffers}<p class="kana" lang="ja">{note.kana}</p>{/if}
        <p class="romaji">{note.romaji}</p>
        <p class="french">{note.french}</p>
      {:else}
        {#if kanaDiffers}<p class="kana" lang="ja">{note.kanji}</p>{/if}
        <p class="romaji">{note.romaji}</p>
        <p class="french">{note.french}</p>
      {/if}
    {/if}
  </div>

  <footer>
    <span>{LEVEL_LABELS[card.level]}</span>
    {#if note.frequency}
      <span>fréquence {note.frequency.score} ({note.frequency.source})</span>
    {/if}
  </footer>
{:else}
  {@const register = card.register === 'polite' ? 'poli' : 'neutre'}
  {@const details = [register, card.conjugation.hint].filter(Boolean).join(', ')}
  <div class="face">
    {#if card.direction === 'fr-jp'}
      <p class="french question">{card.form.french}</p>
      <p class="register">({details})</p>
    {:else}
      <p class="japanese question" lang="ja">{card.form.kanji}</p>
      <p class="kana" lang="ja">{card.form.kana}</p>
    {/if}

    {#if revealed}
      <hr />
      {#if card.direction === 'fr-jp'}
        <p class="japanese" lang="ja">{card.form.kanji}</p>
        <p class="kana" lang="ja">{card.form.kana}</p>
        <p class="romaji">{card.form.romaji}</p>
      {:else}
        <p class="romaji">{card.form.romaji}</p>
        <p class="french">{card.form.french}</p>
      {/if}

      <dl>
        <dt>forme</dt>
        <dd>
          {card.conjugation.label}
          {card.polarity === 'positive' ? 'affirmatif' : 'négatif'}
          {card.conjugation.forms.some((f) => f.startsWith('polite')) ? register : ''}
        </dd>
        <dt>verbe</dt>
        <dd><span lang="ja">{card.note.kanji}</span> <span class="kana" lang="ja">{card.note.kana}</span> <span class="romaji">{card.note.romaji}</span></dd>
        <dt>sens</dt>
        <dd>{card.note.french}</dd>
        <dt>groupe</dt>
        <dd>{groupLabel(card.note.group)}</dd>
      </dl>
    {/if}
  </div>

  <footer>
    <span>{LEVEL_LABELS[card.level]}</span>
    <span>conjugaison</span>
  </footer>
{/if}

<style>
  .face {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.35rem;
    text-align: center;
  }

  p {
    margin: 0;
  }

  .question {
    font-size: clamp(1.6rem, 6vw, 2.2rem);
  }

  .japanese {
    font-family: var(--font-ja);
    font-size: clamp(2.2rem, 10vw, 3.4rem);
    line-height: 1.25;
  }

  .japanese.question {
    font-size: clamp(2.6rem, 12vw, 4rem);
  }

  .kana {
    font-family: var(--font-ja);
    color: var(--kana);
    font-size: 1.35rem;
  }

  .romaji {
    color: var(--muted);
    font-style: italic;
  }

  .french {
    font-size: 1.3rem;
  }

  .french.question {
    font-size: clamp(1.6rem, 6vw, 2.2rem);
  }

  .register {
    color: var(--muted);
    font-size: 0.95rem;
  }

  hr {
    width: 100%;
    border: none;
    border-top: 1px solid var(--line);
    margin: 1rem 0;
  }

  dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.3rem 1rem;
    margin: 1.25rem 0 0;
    padding: 0.85rem 1rem;
    border: 1px solid var(--line);
    border-radius: 10px;
    text-align: left;
    font-size: 0.95rem;
  }

  dt {
    color: var(--muted);
  }

  dd {
    margin: 0;
  }

  dd .kana {
    font-size: 1rem;
  }

  footer {
    display: flex;
    justify-content: space-between;
    margin-top: 2rem;
    padding-top: 0.5rem;
    border-top: 1px dashed var(--line);
    color: var(--muted);
    font-size: 0.8rem;
  }
</style>
