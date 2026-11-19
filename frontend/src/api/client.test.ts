import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError } from './client'

function respondWith(status: number, body: unknown) {
  const fetchMock = vi
    .fn()
    .mockResolvedValue(
      new Response(typeof body === 'string' ? body : JSON.stringify(body), { status }),
    )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api client', () => {
  it('posts JSON and returns the parsed body', async () => {
    const listing = { folder: { id: 'f', name: 'F' }, files: [], skipped: [], truncated: false }
    const fetchMock = respondWith(200, listing)

    await expect(api.listFolder('https://drive.google.com/x', true)).resolves.toEqual(listing)

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/folders/list')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({
      link: 'https://drive.google.com/x',
      recursive: true,
    })
  })

  it('turns the backend error envelope into an ApiError', async () => {
    respondWith(404, { error: { code: 'folder_not_found', message: 'Folder not found.' } })

    const error = await api.listFolder('x', false).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      code: 'folder_not_found',
      message: 'Folder not found.',
      status: 404,
    })
  })

  it('reports HTTP errors without an envelope', async () => {
    respondWith(502, '<html>Bad gateway</html>')

    await expect(api.health()).rejects.toMatchObject({ code: 'http_error', status: 502 })
  })

  it('reports network failures in plain words', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(api.health()).rejects.toMatchObject({
      code: 'network_error',
      message: expect.stringContaining('Cannot reach the server') as unknown,
    })
  })

  it('escapes job ids in URLs', () => {
    expect(api.exportUrl('a/b')).toBe('/api/jobs/a%2Fb/export')
  })
})
