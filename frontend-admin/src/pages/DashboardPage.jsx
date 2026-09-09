import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  listStoreOrders,
  getOrder,
  updateStatus,
  deleteOrder,
  closeSession,
  STATUS_LABEL,
  nextStatus,
} from '../api/orders.js'
import { useOrderStream } from '../hooks/useOrderStream.js'

const won = (n) => `${(n ?? 0).toLocaleString('ko-KR')}원`
const shortId = (id) => (id ? id.slice(0, 8) : '')

// US-ORDER-09/10/11/12, US-SESSION-02/03.
export default function DashboardPage() {
  const [orders, setOrders] = useState([])
  const [filterTable, setFilterTable] = useState('')
  const [selected, setSelected] = useState(null) // full OrderOut
  const [error, setError] = useState(null)
  const [flash, setFlash] = useState({}) // order_id -> highlight timestamp

  // BR-FA06/BR-FA10 — authoritative refetch (also used as SSE resync).
  const refetch = useCallback(async () => {
    try {
      const list = await listStoreOrders(filterTable ? { table_id: filterTable } : {})
      setOrders(list || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }, [filterTable])

  useEffect(() => {
    refetch()
  }, [refetch])

  // SSE (BR-FA10): apply incremental events; resync full list on (re)connect.
  const onEvent = useCallback((ev) => {
    if (ev.type === 'order_created') {
      setFlash((f) => ({ ...f, [ev.order_id]: Date.now() }))
      refetch()
    } else if (ev.type === 'order_status') {
      setOrders((os) => os.map((o) => (o.id === ev.order_id ? { ...o, status: ev.status } : o)))
      setSelected((s) => (s && s.id === ev.order_id ? { ...s, status: ev.status } : s))
    } else if (ev.type === 'order_deleted') {
      setOrders((os) => os.filter((o) => o.id !== ev.order_id))
      setSelected((s) => (s && s.id === ev.order_id ? null : s))
    } else if (ev.type === 'session_closed') {
      refetch()
      setSelected((s) => (s && s.session_id === ev.session_id ? null : s))
    }
  }, [refetch])

  const { connected } = useOrderStream({ onEvent, onResync: refetch })

  // Distinct tables present (for the filter dropdown, US-ORDER-12).
  const tables = useMemo(
    () => Array.from(new Set(orders.map((o) => o.table_id))).sort(),
    [orders],
  )

  // Group orders by table for the grid (BR-FA06).
  const grid = useMemo(() => {
    const by = new Map()
    for (const o of orders) {
      if (!by.has(o.table_id)) by.set(o.table_id, [])
      by.get(o.table_id).push(o)
    }
    return Array.from(by.entries()).map(([table_id, list]) => ({
      table_id,
      list: [...list].sort((a, b) => a.order_no - b.order_no),
    }))
  }, [orders])

  const openDetail = async (id) => {
    setError(null)
    try {
      setSelected(await getOrder(id)) // BR-FA07 — always server-fresh
    } catch (err) {
      setError(err.message)
    }
  }

  const doStatus = async (order, status) => {
    try {
      const updated = await updateStatus(order.id, status)
      setSelected(updated)
      setOrders((os) => os.map((o) => (o.id === order.id ? { ...o, status: updated.status } : o)))
    } catch (err) {
      setError(err.message)
    }
  }

  const doDelete = async (order) => {
    if (!window.confirm(`주문 #${order.order_no}을(를) 삭제할까요?`)) return
    try {
      await deleteOrder(order.id)
      setOrders((os) => os.filter((o) => o.id !== order.id))
      setSelected(null)
    } catch (err) {
      setError(err.message)
    }
  }

  const doCloseSession = async (order) => {
    if (!window.confirm(`테이블 ${shortId(order.table_id)}의 세션을 종료할까요?`)) return
    try {
      await closeSession(order.session_id)
      setSelected(null)
      refetch()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="dashboard">
      <div className="page-head">
        <h2>실시간 주문 모니터링</h2>
        <div className="head-controls">
          <span className={connected ? 'dot on' : 'dot off'} title={connected ? '실시간 연결됨' : '재연결 중…'} />
          <span className="muted">{connected ? '실시간' : '재연결 중…'}</span>
          <select value={filterTable} onChange={(e) => setFilterTable(e.target.value)}>
            <option value="">전체 테이블</option>
            {tables.map((t) => (
              <option key={t} value={t}>테이블 {shortId(t)}</option>
            ))}
          </select>
          <button className="btn ghost" onClick={refetch}>새로고침</button>
        </div>
      </div>

      {error && <div className="error" role="alert">{error}</div>}

      <div className="split">
        <div className="grid">
          {grid.length === 0 && <div className="muted empty">진행 중인 주문이 없습니다.</div>}
          {grid.map(({ table_id, list }) => (
            <div key={table_id} className="table-card">
              <div className="table-card-head">테이블 {shortId(table_id)}</div>
              {list.map((o) => (
                <button
                  key={o.id}
                  className={`order-chip status-${o.status} ${flash[o.id] ? 'flash' : ''} ${selected?.id === o.id ? 'sel' : ''}`}
                  onClick={() => openDetail(o.id)}
                >
                  <span>#{o.order_no}</span>
                  <span className="chip-status">{STATUS_LABEL[o.status]}</span>
                  <span className="chip-total">{won(o.total)}</span>
                </button>
              ))}
            </div>
          ))}
        </div>

        <aside className="detail">
          {!selected ? (
            <div className="muted empty">주문을 선택하면 상세가 표시됩니다.</div>
          ) : (
            <div className="card">
              <h3>주문 #{selected.order_no}</h3>
              <div className="muted">테이블 {shortId(selected.table_id)} · 세션 {shortId(selected.session_id)}</div>
              <ul className="items">
                {selected.items?.map((it, i) => (
                  <li key={i}>
                    <span>{it.name}</span>
                    <span className="muted">{won(it.unit_price)} × {it.qty}</span>
                  </li>
                ))}
              </ul>
              <div className="total-row"><span>합계</span><strong>{won(selected.total)}</strong></div>
              <div className="status-row">
                현재 상태: <strong>{STATUS_LABEL[selected.status]}</strong>
              </div>
              <div className="actions">
                {nextStatus(selected.status) && (
                  <button className="btn primary" onClick={() => doStatus(selected, nextStatus(selected.status))}>
                    {STATUS_LABEL[nextStatus(selected.status)]}(으)로 변경
                  </button>
                )}
                {selected.status !== 'pending' && (
                  <button className="btn" onClick={() => doStatus(selected, 'pending')}>대기중으로</button>
                )}
                <button className="btn danger" onClick={() => doDelete(selected)}>주문 삭제</button>
                <button className="btn warn" onClick={() => doCloseSession(selected)}>세션 종료</button>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
