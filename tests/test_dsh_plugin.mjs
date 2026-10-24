import assert from 'node:assert/strict'
import test from 'node:test'
import { createHabitatClient, localServiceUrl } from '../integrations/dsh-plugin/api-client.js'

test('accepts only local HTTP service URLs', () => {
  assert.equal(localServiceUrl('http://127.0.0.1:8765'), 'http://127.0.0.1:8765')
  assert.equal(localServiceUrl('http://[::1]:8765'), 'http://[::1]:8765')
  for (const url of [
    'https://127.0.0.1:8765',
    'http://example.com:8765',
    'http://localhost:8765/path',
    'http://user:pass@localhost:8765',
  ]) {
    assert.throws(() => localServiceUrl(url), /only accepts a local HTTP service URL/)
  }
})

test('lists residents using the configured loopback origin and forwards cancellation', async () => {
  let seen
  const signal = new AbortController().signal
  const client = createHabitatClient('http://127.0.0.1:8765', async (url, options) => {
    seen = { url: url.href, options }
    return new Response('{"residents":[]}', { status: 200 })
  })
  assert.deepEqual(await client.listResidents(signal), { residents: [] })
  assert.equal(seen.url, 'http://127.0.0.1:8765/residents')
  assert.equal(seen.options.signal, signal)
})

test('submits URL-encoded resident actions as JSON', async () => {
  let seen
  const client = createHabitatClient('http://localhost:8765', async (url, options) => {
    seen = { url: url.href, options }
    return new Response('{"decision":{"allowed":false}}', { status: 200 })
  })
  const result = await client.submitAction('resident/one', 'attack')
  assert.deepEqual(result, { decision: { allowed: false } })
  assert.equal(seen.url, 'http://localhost:8765/residents/resident%2Fone/actions')
  assert.equal(seen.options.method, 'POST')
  assert.equal(seen.options.headers['Content-Type'], 'application/json')
  assert.deepEqual(JSON.parse(seen.options.body), { kind: 'attack' })
})

test('validates event limits and rejects failed or malformed service responses', async () => {
  const client = createHabitatClient('http://127.0.0.1:8765', async () => new Response('unavailable', { status: 503 }))
  assert.throws(() => client.recentEvents(0), /limit must be an integer/)
  await assert.rejects(client.recentEvents(10), /HTTP 503/)

  const invalidJson = createHabitatClient('http://127.0.0.1:8765', async () => new Response('not-json', { status: 200 }))
  await assert.rejects(invalidJson.listResidents(), /invalid JSON response/)
})
