import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMenusGrouped } from '../api/menus.js'
import { createOrder } from '../api/orders.js'
import { useCart } from '../cart/CartContext.jsx'

const won = (n) => `${n.toLocaleString('ko-KR')}원`

// US-MENU-01/02/03 + US-ORDER-01~06: browse category-grouped menu, manage the
// local cart, and confirm the order.
export default function MenuPage() {
  const navigate = useNavigate()
  const cart = useCart()
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [detail, setDetail] = useState(null) // menu shown in the detail modal
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)
  const [placed, setPlaced] = useState(null) // { order_no } after success

  useEffect(() => {
    let alive = true
    getMenusGrouped()
      .then((g) => alive && setGroups(g))
      .catch((err) => alive && setLoadError(err.message || '메뉴를 불러오지 못했습니다.'))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [])

  const confirmOrder = async () => {
    if (cart.items.length === 0 || submitting) return
    setSubmitting(true)
    setSubmitError(null)
    try {
      const order = await createOrder(cart.items)
      cart.clear() // BR-FC08: clear only on success
      setPlaced({ order_no: order.order_no })
      // Brief confirmation, then jump to the order history screen. [BR-FC09]
      setTimeout(() => navigate('/orders'), 1200)
    } catch (err) {
      // BR-FC08: keep the cart on failure and surface the error.
      setSubmitError(err.message || '주문에 실패했습니다. 다시 시도해 주세요.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="center muted">메뉴 불러오는 중…</div>
  if (loadError) return <div className="center error" role="alert">{loadError}</div>

  return (
    <div className="menu-layout">
      <section className="menu-list">
        {groups.length === 0 && <p className="muted">등록된 메뉴가 없습니다.</p>}
        {groups.map((group) => (
          <div key={group.category} className="menu-group">
            <h2 className="category">{group.category}</h2>
            <div className="menu-grid">
              {group.items.map((m) => (
                <div key={m.id} className="menu-card" data-testid="menu-card">
                  {m.image_url && <img src={m.image_url} alt={m.name} className="menu-img" />}
                  <div className="menu-body">
                    <button className="menu-name-btn" onClick={() => setDetail(m)}>
                      {m.name}
                    </button>
                    <div className="menu-price">{won(m.price)}</div>
                    <button className="add-btn" onClick={() => cart.add(m)}>
                      담기
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>

      <aside className="cart-panel">
        <h2>장바구니</h2>
        {cart.items.length === 0 ? (
          <p className="muted">담긴 메뉴가 없습니다.</p>
        ) : (
          <ul className="cart-items">
            {cart.items.map((it) => (
              <li key={it.menu_id} className="cart-item" data-testid="cart-item">
                <span className="ci-name">{it.name}</span>
                <div className="qty">
                  <button aria-label="수량 감소" onClick={() => cart.setQty(it.menu_id, it.qty - 1)}>
                    −
                  </button>
                  <span data-testid="cart-qty">{it.qty}</span>
                  <button aria-label="수량 증가" onClick={() => cart.setQty(it.menu_id, it.qty + 1)}>
                    +
                  </button>
                </div>
                <span className="ci-sub">{won(it.price * it.qty)}</span>
                <button className="ci-remove" aria-label="삭제" onClick={() => cart.remove(it.menu_id)}>
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}

        <div className="cart-total">
          <span>합계</span>
          <strong data-testid="cart-total">{won(cart.total)}</strong>
        </div>

        {submitError && <p className="error" role="alert">{submitError}</p>}
        {placed && (
          <p className="success" role="status">
            주문 완료! 주문번호 <strong>#{placed.order_no}</strong>
          </p>
        )}

        <div className="cart-actions">
          <button className="ghost" disabled={cart.items.length === 0} onClick={cart.clear}>
            비우기
          </button>
          <button
            className="primary"
            disabled={cart.items.length === 0 || submitting}
            onClick={confirmOrder}
          >
            {submitting ? '주문 중…' : '주문하기'}
          </button>
        </div>
      </aside>

      {detail && (
        <div className="modal-backdrop" onClick={() => setDetail(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            {detail.image_url && <img src={detail.image_url} alt={detail.name} className="modal-img" />}
            <h3>{detail.name}</h3>
            {detail.description && <p className="desc">{detail.description}</p>}
            <div className="menu-price">{won(detail.price)}</div>
            <div className="modal-actions">
              <button className="ghost" onClick={() => setDetail(null)}>닫기</button>
              <button
                className="primary"
                onClick={() => {
                  cart.add(detail)
                  setDetail(null)
                }}
              >
                담기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
