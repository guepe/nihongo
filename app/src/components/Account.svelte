<script lang="ts">
  import { api, ApiError, type Session } from '../lib/api'
  import type { SyncStatus } from '../lib/sync'

  let { session, status, onsync, onlogout }: {
    session: Session
    status: SyncStatus
    onsync: () => void
    onlogout: () => void
  } = $props()

  let invitation = $state<{ link: string; days: number } | null>(null)
  let error = $state<string | null>(null)
  let copied = $state(false)

  async function invite() {
    error = null
    try {
      const result = await api<{ code: string; days: number }>('POST', 'invitations', {}, session.token)
      invitation = { link: `${location.origin}/#invitation=${result.code}`, days: result.days }
    } catch (e) {
      error = e instanceof ApiError ? e.message : String(e)
    }
  }

  async function share() {
    if (!invitation) return
    const text = 'Rejoins-moi sur hachi pour réviser le japonais :'
    if (navigator.share) {
      await navigator.share({ title: 'hachi', text, url: invitation.link }).catch(() => {})
    } else {
      await navigator.clipboard.writeText(invitation.link)
      copied = true
    }
  }
</script>

<section>
  <h2>Compte</h2>
  <p class="who">{session.user.name} <span>{session.user.email}</span></p>

  <div class="row">
    <p class="status" class:warning={status.error || status.pending > 0}>
      {#if status.syncing}
        Synchronisation…
      {:else if status.error}
        {status.error}{status.pending ? ` — ${status.pending} révision${status.pending > 1 ? 's' : ''} en attente` : ''}
      {:else if status.pending}
        {status.pending} révision{status.pending > 1 ? 's' : ''} en attente d'envoi
      {:else}
        Toutes les révisions sont synchronisées.
      {/if}
    </p>
    <button class="link" onclick={onsync} disabled={status.syncing}>Synchroniser</button>
  </div>

  {#if session.user.is_admin}
    <div class="row">
      <p>Inviter une personne à créer son compte.</p>
      <button class="link" onclick={invite}>Créer une invitation</button>
    </div>
    {#if invitation}
      <div class="invitation">
        <code>{invitation.link}</code>
        <button class="primary" onclick={share}>{copied ? 'Lien copié' : 'Partager le lien'}</button>
        <p class="hint">Valable {invitation.days} jours, pour un seul compte.</p>
      </div>
    {/if}
    {#if error}<p class="error" role="alert">{error}</p>{/if}
  {/if}

  <button class="logout" onclick={onlogout}>Se déconnecter</button>
</section>

<style>
  section {
    padding-bottom: calc(2rem + env(safe-area-inset-bottom));
  }

  h2 {
    margin: 0 0 0.75rem;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
  }

  p {
    margin: 0;
  }

  .who {
    font-weight: 600;
  }

  .who span {
    margin-left: 0.4rem;
    color: var(--muted);
    font-weight: 400;
  }

  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--line);
  }

  .status {
    color: var(--good);
  }

  .status.warning {
    color: var(--hard);
  }

  .invitation {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 0.85rem 0;
  }

  code {
    padding: 0.6rem 0.75rem;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface);
    font-size: 0.85rem;
    overflow-wrap: anywhere;
    user-select: all;
  }

  .hint {
    color: var(--muted);
    font-size: 0.85rem;
  }

  .error {
    color: var(--again);
  }

  .logout {
    width: 100%;
    margin-top: 1.5rem;
    padding: 0.8rem;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--surface);
    color: var(--again);
  }
</style>
