import { Navigate } from 'react-router-dom'
import { useSession } from '../session/SessionContext.jsx'

// BR-FC04: block menu/orders routes unless a session is active.
export default function SessionRoute({ children }) {
  const { session, loading } = useSession()
  if (loading) return <div className="center muted">불러오는 중…</div>
  if (!session) return <Navigate to="/start" replace />
  return children
}
