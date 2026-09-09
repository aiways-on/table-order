import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react'

// US-ORDER-01~04 / BR-FC07: local-only cart. Persisted to localStorage so it
// survives a reload. Items carry name/price for display, but only menu_id+qty
// are sent on confirm — the server owns pricing (BR-FC06).

const STORAGE_KEY = 'customer_cart'
const CartContext = createContext(null)

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const items = raw ? JSON.parse(raw) : []
    return Array.isArray(items) ? items : []
  } catch {
    return []
  }
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => load())

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  }, [items])

  const add = useCallback((menu) => {
    setItems((prev) => {
      const found = prev.find((it) => it.menu_id === menu.id)
      if (found) {
        return prev.map((it) =>
          it.menu_id === menu.id ? { ...it, qty: it.qty + 1 } : it
        )
      }
      return [...prev, { menu_id: menu.id, name: menu.name, price: menu.price, qty: 1 }]
    })
  }, [])

  const setQty = useCallback((menuId, qty) => {
    setItems((prev) => {
      if (qty < 1) return prev.filter((it) => it.menu_id !== menuId)
      return prev.map((it) => (it.menu_id === menuId ? { ...it, qty } : it))
    })
  }, [])

  const remove = useCallback((menuId) => {
    setItems((prev) => prev.filter((it) => it.menu_id !== menuId))
  }, [])

  const clear = useCallback(() => setItems([]), [])

  const total = useMemo(
    () => items.reduce((sum, it) => sum + it.price * it.qty, 0),
    [items]
  )
  const count = useMemo(
    () => items.reduce((sum, it) => sum + it.qty, 0),
    [items]
  )

  return (
    <CartContext.Provider value={{ items, add, setQty, remove, clear, total, count }}>
      {children}
    </CartContext.Provider>
  )
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used within CartProvider')
  return ctx
}
