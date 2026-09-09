import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { CartProvider, useCart } from './CartContext.jsx'

const wrapper = ({ children }) => <CartProvider>{children}</CartProvider>
const menu = (id, price) => ({ id, name: `M${id}`, price })

describe('CartContext (US-ORDER-01~04 / BR-FC07)', () => {
  beforeEach(() => localStorage.clear())

  it('adds items and increments qty on duplicate add', () => {
    const { result } = renderHook(() => useCart(), { wrapper })
    act(() => result.current.add(menu('a', 4000)))
    act(() => result.current.add(menu('a', 4000)))
    expect(result.current.items).toHaveLength(1)
    expect(result.current.items[0].qty).toBe(2)
    expect(result.current.count).toBe(2)
  })

  it('computes live total = Σ price × qty', () => {
    const { result } = renderHook(() => useCart(), { wrapper })
    act(() => result.current.add(menu('a', 4000)))
    act(() => result.current.add(menu('b', 3000)))
    act(() => result.current.setQty('a', 2))
    expect(result.current.total).toBe(4000 * 2 + 3000)
  })

  it('removes an item when qty drops below 1', () => {
    const { result } = renderHook(() => useCart(), { wrapper })
    act(() => result.current.add(menu('a', 4000)))
    act(() => result.current.setQty('a', 0))
    expect(result.current.items).toHaveLength(0)
  })

  it('clears the whole cart', () => {
    const { result } = renderHook(() => useCart(), { wrapper })
    act(() => result.current.add(menu('a', 4000)))
    act(() => result.current.clear())
    expect(result.current.items).toHaveLength(0)
    expect(result.current.total).toBe(0)
  })

  it('persists to localStorage so a reload keeps the cart (US-ORDER-03)', () => {
    const first = renderHook(() => useCart(), { wrapper })
    act(() => first.result.current.add(menu('a', 4000)))
    // Fresh provider = simulated reload; state hydrates from localStorage.
    const second = renderHook(() => useCart(), { wrapper })
    expect(second.result.current.items).toHaveLength(1)
    expect(second.result.current.items[0].menu_id).toBe('a')
  })
})
