<script lang="ts">
  import { api, ApiError, type Session } from '../lib/api'

  let { device, onlogin }: { device: string; onlogin: (session: Session) => void } = $props()

  // An invitation link looks like https://<site>/#invitation=<code>
  const invited = new URLSearchParams(location.hash.slice(1)).get('invitation') ?? ''

  let mode = $state<'login' | 'register'>(invited ? 'register' : 'login')
  let code = $state(invited)
  let name = $state('')
  let email = $state('')
  let password = $state('')
  let error = $state<string | null>(null)
  let busy = $state(false)

  async function submit(event: SubmitEvent) {
    event.preventDefault()
    error = null
    busy = true
    try {
      const session = mode === 'login'
        ? await api<Session>('POST', 'login', { email, password, device })
        : await api<Session>('POST', 'register', { code, name, email, password, device })
      if (invited) history.replaceState(null, '', location.pathname)
      onlogin(session)
    } catch (e) {
      error = e instanceof ApiError ? e.message : String(e)
    } finally {
      busy = false
    }
  }
</script>

<div class="login">
  <h1><span lang="ja">蜂</span> hachi</h1>

  <form onsubmit={submit}>
    {#if mode === 'register'}
      <label>
        Code d'invitation
        <input bind:value={code} required autocomplete="off" autocapitalize="off" spellcheck="false" />
      </label>
      <label>
        Prénom
        <input bind:value={name} required autocomplete="given-name" />
      </label>
    {/if}
    <label>
      Adresse e-mail
      <input type="email" bind:value={email} required autocomplete="email" autocapitalize="off" />
    </label>
    <label>
      Mot de passe
      <input type="password" bind:value={password} required minlength={mode === 'register' ? 8 : undefined}
        autocomplete={mode === 'login' ? 'current-password' : 'new-password'} />
    </label>

    {#if error}<p class="error" role="alert">{error}</p>{/if}

    <button class="primary" type="submit" disabled={busy}>
      {mode === 'login' ? 'Se connecter' : 'Créer mon compte'}
    </button>
  </form>

  <button class="link" onclick={() => { mode = mode === 'login' ? 'register' : 'login'; error = null }}>
    {mode === 'login' ? 'J\'ai une invitation : créer un compte' : 'J\'ai déjà un compte : me connecter'}
  </button>
</div>

<style>
  .login {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    padding: 12vh 0 2rem;
  }

  h1 {
    margin: 0 0 1rem;
    font-size: 2.4rem;
    font-weight: 600;
    text-align: center;
  }

  h1 span {
    font-family: var(--font-ja);
    color: var(--accent);
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.9rem;
    color: var(--muted);
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

  .primary {
    min-height: 3.25rem;
    margin-top: 0.5rem;
  }

  .error {
    margin: 0;
    color: var(--again);
  }

  .link {
    align-self: center;
  }
</style>
