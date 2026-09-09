import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useSession } from '../session/SessionContext.jsx'

// US-AUTH-05: table session start. If a session is already stored, the tablet
// skips this screen entirely (auto-login, BR-FC02).
export default function StartPage() {
  const { session, start } = useSession()
  const navigate = useNavigate()
  const [storeCode, setStoreCode] = useState('')
  const [tableNo, setTableNo] = useState('')
  const [tablePassword, setTablePassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  if (session) return <Navigate to="/menu" replace />

  const onSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await start({ storeCode, tableNo, tablePassword })
      navigate('/menu', { replace: true })
    } catch (err) {
      setError(err.message || '입장에 실패했습니다.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="center">
      <form className="card start-card" onSubmit={onSubmit}>
        <h1>테이블 입장</h1>
        <label>
          매장 코드
          <input
            value={storeCode}
            onChange={(e) => setStoreCode(e.target.value)}
            placeholder="예: CAFE01"
            autoComplete="off"
            required
          />
        </label>
        <label>
          테이블 번호
          <input
            type="number"
            min="1"
            value={tableNo}
            onChange={(e) => setTableNo(e.target.value)}
            required
          />
        </label>
        <label>
          테이블 비밀번호
          <input
            type="password"
            value={tablePassword}
            onChange={(e) => setTablePassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? '입장 중…' : '입장하기'}
        </button>
      </form>
    </div>
  )
}
