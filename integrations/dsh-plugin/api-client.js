export function localServiceUrl(value) {
  const url = new URL(value)
  const localHosts = new Set(['127.0.0.1', '::1', '[::1]', 'localhost'])
  if (url.protocol !== 'http:' || !localHosts.has(url.hostname.toLowerCase()) ||
      url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
    throw new Error('Cyber Habitat DSH plugin only accepts a local HTTP service URL')
  }
  return url.origin
}

export function createHabitatClient(value, fetchImpl = globalThis.fetch) {
  const baseUrl = localServiceUrl(value)

  async function request(path, init = {}, signal) {
    const response = await fetchImpl(new URL(path, `${baseUrl}/`), {
      ...init,
      signal,
      headers: { 'Content-Type': 'application/json', ...init.headers },
    })
    const text = await response.text()
    if (!response.ok) throw new Error(`Cyber Habitat returned HTTP ${response.status}`)
    try {
      return JSON.parse(text)
    } catch {
      throw new Error('Cyber Habitat returned an invalid JSON response')
    }
  }

  return {
    listResidents(signal) {
      return request('/residents', {}, signal)
    },
    recentEvents(limit, signal) {
      if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
        throw new Error('limit must be an integer from 1 to 100')
      }
      return request(`/events?limit=${limit}`, {}, signal)
    },
    submitAction(residentId, kind, signal) {
      return request(`/residents/${encodeURIComponent(residentId)}/actions`, {
        method: 'POST',
        body: JSON.stringify({ kind }),
      }, signal)
    },
  }
}
