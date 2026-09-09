import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listMyOrders, statusLabel } from '../api/orders.js'
import { useSession } from '../session/SessionContext.jsx'
import { useOrderStream } from '../hooks/useOrderStream.js'

const won = (n) => `${n.toLocaleString('ko-KR')}원`

// US-ORDER-07/08: this session's orders with realtime status. SSE events just
// trigger a full re-fetch (resync) to keep the list authoritative. [BR-FC11..14]
export default function OrdersPage() {
  const { session, clear } = useSession()
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [error, setError] = useState(null)

  const refetch = useCallback(async () => {
    try {
      const data = await listMyOrders()
      setOrders(data || [])
      setError(null)
    } catch (err) {
      setError(err.message || '주문 내역을 불러오지 못했습니다.')
    }
  }, [])

  useEffect(() => {
    refetch()
  }, [refetch])

  const onEvent = useCallback(
    (evt) => {
      if (evt?.type === 'session_closed') {
        // BR-FC13: server closed the session → drop it and return to /start.
        clear()
        navigate('/start', { replace: true })
        return
      }
      // order_created / order_status / order_deleted → resync. [BR-FC12]
      refetch()
    },
    [clear, navigate, refetch]
  )

  const { connected } = useOrderStream({
    token: session?.session_token,
    onEvent,
    onResync: refetch, // heal gaps on (re)connect [BR-FC14]
  })

  return (
    <div className="orders-page">
      <div className="orders-head">
        <h1>주문 내역</h1>
        <span className={connected ? 'live on' : 'live off'} data-testid="live-indicator">
          {connected ? '실시간 연결됨' : '연결 대기중…'}
        </span>
      </div>

      {error && <p className="error" role="alert">{error}</p>}
      {orders.length === 0 ? (
        <p className="muted">아직 주문이 없습니다.</p>
      ) : (
        <ul className="order-list">
          {orders.map((o) => (
            <li key={o.id} className="order-card" data-testid="order-card">
              <div className="order-top">
                <span className="order-no">주문 #{o.order_no}</span>
                <span className={`status status-${o.status}`} data-testid="order-status">
                  {statusLabel(o.status)}
                </span>
              </div>
              <ul className="order-items">
                {o.items.map((it, i) => (
                  <li key={i}>
                    {it.name} × {it.qty}
                    <span className="oi-sub">{won(it.unit_price * it.qty)}</span>
                  </li>
                ))}
              </ul>
              <div className="order-total">
                합계 <strong>{won(o.total)}</strong>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
