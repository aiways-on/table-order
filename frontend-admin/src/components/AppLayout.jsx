import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'

const NAV = [
  { to: '/dashboard', label: '대시보드' },
  { to: '/menus', label: '메뉴 관리' },
  { to: '/tables', label: '테이블 설정' },
  { to: '/history', label: '주문 이력' },
]

export default function AppLayout() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  const onLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">테이블오더 · 관리자</div>
        <nav className="nav">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="topbar-right">
          <span className="muted store-id" title="매장 ID">{auth?.store_id?.slice(0, 8)}</span>
          <button className="btn ghost" onClick={onLogout}>로그아웃</button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
