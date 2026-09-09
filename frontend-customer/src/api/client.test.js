import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api, ApiError, setSessionToken, setUnauthorizedHandler } from './client.js'

describe('api client', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })
  afterEach(() => {
    vi.restoreAllMocks()
    setUnauthorizedHandler(null)
    setSessionToken(null)
  })

  it('sends the X-Session-Token header when a token is set (BR-FC01)', async () => {
    setSessionToken('tok-123')
    global.fetch.mockResolvedValue(new Response(JSON.stringify({ ok: 1 }), { status: 200 }))
    await api.get('/orders')
    const [, opts] = global.fetch.mock.calls[0]
    expect(opts.headers['X-Session-Token']).toBe('tok-123')
  })

  it('omits the token header when logged out', async () => {
    global.fetch.mockResolvedValue(new Response(JSON.stringify({ ok: 1 }), { status: 200 }))
    await api.get('/menus')
    const [, opts] = global.fetch.mock.calls[0]
    expect(opts.headers['X-Session-Token']).toBeUndefined()
  })

  it('JSON-encodes bodies with a Content-Type header', async () => {
    global.fetch.mockResolvedValue(new Response(JSON.stringify({ order_no: 1 }), { status: 201 }))
    await api.post('/orders', { items: [{ menu_id: 'm1', qty: 2 }] })
    const [, opts] = global.fetch.mock.calls[0]
    expect(opts.method).toBe('POST')
    expect(opts.headers['Content-Type']).toBe('application/json')
    expect(JSON.parse(opts.body)).toMatchObject({ items: [{ menu_id: 'm1', qty: 2 }] })
  })

  it('returns null for 204 No Content', async () => {
    global.fetch.mockResolvedValue(new Response(null, { status: 204 }))
    await expect(api.del('/orders/o1')).resolves.toBeNull()
  })

  it('fires the unauthorized handler and throws on 401 (BR-FC03)', async () => {
    const onUnauth = vi.fn()
    setUnauthorizedHandler(onUnauth)
    global.fetch.mockResolvedValue(new Response(null, { status: 401 }))
    await expect(api.get('/orders')).rejects.toBeInstanceOf(ApiError)
    expect(onUnauth).toHaveBeenCalledOnce()
  })

  it('surfaces the backend {error:{message}} shape on non-2xx', async () => {
    global.fetch.mockResolvedValue(
      new Response(JSON.stringify({ error: { status: 422, message: '메뉴를 찾을 수 없습니다' } }), {
        status: 422,
      })
    )
    await expect(api.post('/orders', {})).rejects.toThrow('메뉴를 찾을 수 없습니다')
  })

  it('wraps network failures in a friendly ApiError', async () => {
    global.fetch.mockRejectedValue(new TypeError('failed to fetch'))
    await expect(api.get('/menus')).rejects.toBeInstanceOf(ApiError)
  })
})
