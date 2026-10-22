// End-to-end test of the API. Usage: node api/tests/api.test.mjs http://127.0.0.1:8787 <setup code>
// Needs an empty database: it creates the administrator account.
import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'

const [base, setupCode] = process.argv.slice(2)
async function call(method, path, body, token) {
  const response = await fetch(`${base}/api/${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { 'X-Hachi-Token': token } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  return { status: response.status, data: await response.json() }
}
const review = (at, extra = {}) => ({ id: randomUUID(), kind: 'review', at, device: 'test', deck: 'vocabulary', note: 'IyV$E?.Kg&', card: 'fr-jp', rating: 3, ...extra })
let r

// Accounts
r = await call('GET', 'me')
assert.equal(r.status, 401)
r = await call('POST', 'register', { code: 'wrong', name: 'A', email: 'a@x.be', password: 'motdepasse' })
assert.equal(r.status, 403, 'setup code required for the first account')
r = await call('POST', 'register', { code: setupCode, name: 'Admin', email: 'Admin@X.be', password: 'motdepasse', device: 'mac' })
assert.equal(r.status, 201, JSON.stringify(r.data))
assert.equal(r.data.user.is_admin, true)
assert.equal(r.data.user.email, 'admin@x.be')
const admin = r.data.token
r = await call('POST', 'register', { code: setupCode, name: 'B', email: 'b@x.be', password: 'motdepasse' })
assert.equal(r.status, 403, 'setup code only works once')

r = await call('POST', 'invitations', {}, admin)
assert.equal(r.status, 201)
const invitation = r.data.code
r = await call('POST', 'register', { code: invitation, name: 'Bea', email: 'bea@x.be', password: 'court' })
assert.equal(r.status, 400, 'short password')
r = await call('POST', 'register', { code: invitation, name: 'Bea', email: 'bea@x.be', password: 'motdepasse2' })
assert.equal(r.status, 201)
assert.equal(r.data.user.is_admin, false)
const bea = r.data.token
r = await call('POST', 'register', { code: invitation, name: 'C', email: 'c@x.be', password: 'motdepasse' })
assert.equal(r.status, 403, 'invitation used once')
r = await call('POST', 'invitations', {}, bea)
assert.equal(r.status, 403, 'only the admin invites')

r = await call('POST', 'login', { email: 'admin@x.be', password: 'mauvais' })
assert.equal(r.status, 401)
r = await call('POST', 'login', { email: 'ADMIN@x.be', password: 'motdepasse', device: 'iphone' })
assert.equal(r.status, 200)
const adminPhone = r.data.token
r = await call('GET', 'me', null, adminPhone)
assert.equal(r.data.user.name, 'Admin')

// Events
const now = Date.now()
const first = review(now)
r = await call('POST', 'events', { events: [first, review(now + 1)] }, admin)
assert.deepEqual(r.data, { received: 2, added: 2 })
r = await call('POST', 'events', { events: [first, { id: randomUUID(), kind: 'undo', at: now + 2, device: 'test', target: first.id }] }, adminPhone)
assert.deepEqual(r.data, { received: 2, added: 1 }, 'same event sent twice is ignored')
r = await call('POST', 'events', { events: [review(now, { rating: 5 })] }, admin)
assert.equal(r.status, 400)
r = await call('POST', 'events', { events: [review(now + 3 * 86400000)] }, admin)
assert.equal(r.status, 400, 'event far in the future')

r = await call('GET', 'events?since=0', null, adminPhone)
assert.equal(r.data.events.length, 3)
assert.equal(r.data.events[0].note, 'IyV$E?.Kg&', 'note ids keep their case and symbols')
assert.equal(r.data.events[2].kind, 'undo')
const last = r.data.last
r = await call('GET', `events?since=${last}`, null, admin)
assert.equal(r.data.events.length, 0)
r = await call('GET', 'events?since=0&limit=2', null, admin)
assert.equal(r.data.events.length, 2)
assert.equal(r.data.more, true)
r = await call('GET', 'events?since=0', null, bea)
assert.equal(r.data.events.length, 0, 'users only see their own events')

// Settings: the most recent change wins
r = await call('GET', 'settings', null, admin)
assert.deepEqual(r.data, { settings: null, updated_at: 0 })
r = await call('PUT', 'settings', { settings: { retention: 0.85 }, updated_at: 200 }, admin)
assert.equal(r.data.settings.retention, 0.85)
r = await call('PUT', 'settings', { settings: { retention: 0.95 }, updated_at: 100 }, adminPhone)
assert.equal(r.data.settings.retention, 0.85, 'older change ignored')
assert.equal(r.data.updated_at, 200)

// Logout
r = await call('POST', 'logout', {}, adminPhone)
assert.equal(r.status, 200)
r = await call('GET', 'me', null, adminPhone)
assert.equal(r.status, 401)
r = await call('GET', 'me', null, admin)
assert.equal(r.status, 200, 'other sessions stay open')

// Rate limit: 10 failures per quarter of an hour
let blocked = false
for (let i = 0; i < 12; i++) {
  r = await call('POST', 'login', { email: 'bea@x.be', password: 'faux' })
  if (r.status === 429) blocked = true
}
assert.ok(blocked, 'too many failures are blocked')

r = await call('GET', 'nimporte')
assert.equal(r.status, 404)
console.log('API : tous les tests passent')
