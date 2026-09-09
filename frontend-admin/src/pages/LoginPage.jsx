import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'

// US-AUTH-01/02/03 — admin store login. BR-FA01/BR-FA04.
export default function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ store_code: '', admin_username: '', password: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  if (isAuthenticated) {
    navigate('/dashboard', { replace: true })
  }

  // BR-FA01 — client-side minimums mirror server SEC-05 validation.
  const valid =
    form.store_code.trim() && form.admin_username.trim() && form.password.length >= 8

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (!valid || busy) return
    setBusy(true)
    setError(null)
    try {
      await login(form)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      // BR-FA04 — surface server message (incl. 429 rate-limit) verbatim.
      setError(err.message || '로그인에 실패했습니다.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="center">
      <form className="card login-card" onSubmit={submit}>
        <h1>관리자 로그인</h1>
        <label>
          매장 식별자
          <input value={form.store_code} onChange={set('store_code')} autoFocus />
        </label>
        <label>
          사용자명
          <input value={form.admin_username} onChange={set('admin_username')} />
        </label>
        <label>
          비밀번호
          <input type="password" value={form.password} onChange={set('password')} />
          {form.password && form.password.length < 8 && (
            <span className="hint">8자 이상 입력하세요.</span>
          )}
        </label>
        {error && <div className="error" role="alert">{error}</div>}
        <button className="btn primary" type="submit" disabled={!valid || busy}>
          {busy ? '로그인 중…' : '로그인'}
        </button>
      </form>
    </div>
  )
}
