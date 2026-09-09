import { api } from './client.js'

// Single source of truth for status → 한글 label. Matches the backend
// OrderStatus enum (pending | preparing | done). [BR-FC15]
export const STATUS_LABEL = {
  pending: '접수됨',
  preparing: '준비중',
  done: '준비완료',
}

export function statusLabel(status) {
  return STATUS_LABEL[status] || status
}

// US-ORDER-05: confirm order. Only { menu_id, qty } are sent — the server
// re-fetches the authoritative unit price (client prices are ignored). [BR-FC06]
export function createOrder(items) {
  return api.post('/orders', {
    items: items.map((it) => ({ menu_id: it.menu_id, qty: it.qty })),
  })
}

// US-ORDER-07: current session's orders (server enforces session isolation).
export function listMyOrders({ limit = 100, offset = 0 } = {}) {
  return api.get(`/orders?limit=${limit}&offset=${offset}`)
}
