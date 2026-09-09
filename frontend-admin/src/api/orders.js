import { api } from './client.js'

// US-ORDER-09/12 — store-wide list, optional table/status filter.
export const listStoreOrders = ({ table_id, status } = {}) => {
  const qs = new URLSearchParams()
  if (table_id) qs.set('table_id', table_id)
  if (status) qs.set('status', status)
  const q = qs.toString()
  return api.get(`/orders/store${q ? `?${q}` : ''}`)
}

// US-ORDER-10 — full order detail (always server-fresh, BR-FA07).
export const getOrder = (id) => api.get(`/orders/${id}`)

// US-ORDER-11 — status: 'pending' | 'preparing' | 'done'.
export const updateStatus = (id, status) => api.patch(`/orders/${id}/status`, { status })

// US-SESSION-02 / US-ORDER — admin delete (soft).
export const deleteOrder = (id) => api.del(`/orders/${id}`)

// US-SESSION-03 — close a table's session.
export const closeSession = (sessionId) => api.post(`/sessions/${sessionId}/close`)

// US-SESSION-04 — closed-session order history (read-only).
export const listHistory = () => api.get('/history')

export const ORDER_STATUSES = ['pending', 'preparing', 'done']
export const STATUS_LABEL = { pending: '대기중', preparing: '준비중', done: '완료' }
export const nextStatus = (s) => (s === 'pending' ? 'preparing' : s === 'preparing' ? 'done' : null)
