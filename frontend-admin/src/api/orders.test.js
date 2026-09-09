import { describe, it, expect } from 'vitest'
import { nextStatus, STATUS_LABEL, ORDER_STATUSES } from './orders.js'

describe('order status helpers (BR-FA08)', () => {
  it('advances pending → preparing → done, then stops', () => {
    expect(nextStatus('pending')).toBe('preparing')
    expect(nextStatus('preparing')).toBe('done')
    expect(nextStatus('done')).toBeNull()
  })

  it('labels every backend enum value', () => {
    for (const s of ORDER_STATUSES) {
      expect(STATUS_LABEL[s]).toBeTruthy()
    }
  })
})
