import { useEffect, useState } from 'react'
import { listHistory, STATUS_LABEL } from '../api/orders.js'

const won = (n) => `${(n ?? 0).toLocaleString('ko-KR')}원`
const shortId = (id) => (id ? id.slice(0, 8) : '')
const fmt = (s) => (s ? new Date(s).toLocaleString('ko-KR') : '—')

// US-SESSION-04 — read-only history of closed-session orders. BR-FA14.
export default function HistoryPage() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ;(async () => {
      try {
        setRows((await listHistory()) || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return (
    <div className="history">
      <div className="page-head"><h2>주문 이력</h2></div>
      {error && <div className="error" role="alert">{error}</div>}
      {loading ? (
        <div className="muted">불러오는 중…</div>
      ) : rows.length === 0 ? (
        <div className="muted empty">종료된 세션의 주문 이력이 없습니다.</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>주문번호</th><th>테이블</th><th>항목</th><th>합계</th>
              <th>상태</th><th>주문시각</th><th>세션종료</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>#{r.order_no}</td>
                <td>{shortId(r.table_id)}</td>
                <td>{r.items?.map((it) => `${it.name}×${it.qty}`).join(', ')}</td>
                <td>{won(r.total)}</td>
                <td>{STATUS_LABEL[r.status] || r.status}</td>
                <td>{fmt(r.created_at)}</td>
                <td>{fmt(r.session_closed_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
