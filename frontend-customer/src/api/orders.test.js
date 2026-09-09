import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { STATUS_LABEL, statusLabel, createOrder } from './orders.js'
import { setSessionToken } from './client.js'

describe('order helpers', () => {
  it('labels every backend enum value (BR-FC15)', () => {
    for (const s of ['pending', 'preparing', 'done']) {
      expect(STATUS_LABEL[s]).toBeTruthy()
    }
  })

  it('falls back to the raw status for unknown codes', () => {
    expect(statusLabel('weird')).toBe('weird')
  })
})

describe('createOrder (BR-FC06)', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
    setSessionToken('tok')
  })
  afterEach(() => {
    vi.restoreAllMocks()
    setSessionToken(null)
  })

  it('sends only menu_id + qty, dropping any client-side price/name', async () => {
    global.fetch.mockResolvedValue(new Response(JSON.stringify({ order_no: 1 }), { status: 201 }))
    await createOrder([{ menu_id: 'm1', name: '아메리카노', price: 1, qty: 3 }])
    const [, opts] = global.fetch.mock.calls[0]
    expect(JSON.parse(opts.body)).toEqual({ items: [{ menu_id: 'm1', qty: 3 }] })
  })
})
