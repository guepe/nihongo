<script lang="ts">
  import { registerSW } from 'virtual:pwa-register'

  const HOUR = 60 * 60 * 1000

  let needRefresh = $state(false)

  const update = registerSW({
    onNeedRefresh() {
      needRefresh = true
    },
    onRegisteredSW(_url, registration) {
      // An installed app can stay open for days: look for a new version every hour.
      if (registration) setInterval(() => registration.update(), HOUR)
    },
  })
</script>

{#if needRefresh}
  <div class="banner" role="status">
    <span>Nouvelle version disponible.</span>
    <button class="link" onclick={() => (needRefresh = false)}>Plus tard</button>
    <button class="primary" onclick={() => update(true)}>Mettre à jour</button>
  </div>
{/if}

<style>
  .banner {
    position: fixed;
    left: 50%;
    bottom: calc(5.5rem + env(safe-area-inset-bottom));
    transform: translateX(-50%);
    width: min(32rem, calc(100% - 2rem));
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.6rem 0.6rem 1rem;
    border: 1px solid var(--line);
    border-radius: 14px;
    background: var(--surface);
    box-shadow: 0 6px 24px rgb(0 0 0 / 0.12);
    font-size: 0.95rem;
    z-index: 10;
  }

  span {
    flex: 1;
  }

  .primary {
    padding: 0.5rem 0.9rem;
  }
</style>
