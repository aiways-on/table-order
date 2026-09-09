import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return <div className="center muted">불러오는 중…</div>
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}
