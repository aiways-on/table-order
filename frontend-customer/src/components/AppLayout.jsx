import { NavLink, Outlet } from 'react-router-dom'
import { useSession } from '../session/SessionContext.jsx'
import { useCart } from '../cart/CartContext.jsx'

export default function AppLayout() {
  const { session } = useSession()
  const { count } = useCart()

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-title">테이블 주문</span>
          {session?.table_id && (
            <span className="brand-table" data-testid="table-badge">
              테이블 이용중
            </span>
          )}
        </div>
        <nav className="tabs">
          <NavLink to="/menu" className={({ isActive }) => (isActive ? 'tab active' : 'tab')}>
            메뉴{count > 0 ? ` (${count})` : ''}
          </NavLink>
          <NavLink to="/orders" className={({ isActive }) => (isActive ? 'tab active' : 'tab')}>
            주문내역
          </NavLink>
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
