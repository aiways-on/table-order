import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api, ApiError, setUnauthorizedHandler } from './client.js'

describe('api client', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })
  afterEach(() => {
    vi.restoreAllMocks()
    setUnauthorizedHandler(null)
  })

  it('sends credentials: include on every request (SEC cookie)', async () => {
    global.fetch.mockResolvedValue(new Response(JSON.stringify({ ok: 1 }), { status: 200 }))
    await api.get('/menus/flat')
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/menus/flat',
      expect.objectContaining({ credentials: 'include' }),
    )
  })

  it('JSON-encodes bodies with a Content-Type header', async () => {
    global.fetch.mockResolvedValue(new Response(JSON.stringify({ id: 'm1' }), { status: 201 }))
    await api.post('/menus', { name: '아메리카노', price: 4000, category: '음료' })
    const [, opts] = global.fetch.mock.calls[0]
    expect(opts.method).toBe('POST')
    expect(opts.headers['Content-Type']).toBe('application/json')
    expect(JSON.parse(opts.body)).toMatchObject({ name: '아메리카노', price: 4000 })
  })

  it('returns null for 204 No Content (delete/close)', async () => {
    global.fetch.mockResolvedValue(new Response(null, { status: 204 }))
    await expect(api.del('/orders/o1')).resolves.toBeNull()
  })

  it('fires the unauthorized handler and throws on 401 (BR-FA03)', async () => {
    const onUnauth = vi.fn()
    setUnauthorizedHandler(onUnauth)
    global.fetch.mockResolvedValue(new Response(null, { status: 401 }))
    await expect(api.get('/orders/store')).rejects.toBeInstanceOf(ApiError)
    expect(onUnauth).toHaveBeenCalledOnce()
  })

  it('surfaces server "detail" message on non-2xx (BR-FA15)', async () => {
    global.fetch.mockResolvedValue(
      new Response(JSON.stringify({ detail: '로그인 시도가 너무 많습니다' }), { status: 429 }),
    )
    await expect(api.post('/auth/admin/login', {})).rejects.toThrow('로그인 시도가 너무 많습니다')
  })

  it('wraps network failures in a friendly ApiError', async () => {
    global.fetch.mockRejectedValue(new TypeError('failed to fetch'))
    await expect(api.get('/history')).rejects.toBeInstanceOf(ApiError)
  })
})
