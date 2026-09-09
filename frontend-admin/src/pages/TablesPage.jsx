import { useState } from 'react'
import { setupTable } from '../api/auth.js'

// US-AUTH-04 — one-time tablet setup. BR-FA05.
export default function TablesPage() {
  const [form, setForm] = useState({ table_no: '', table_password: '' })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const numOk = Number.isInteger(Number(form.table_no)) && Number(form.table_no) >= 1
  const pwOk = form.table_password.length >= 4
  const valid = numOk && pwOk

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (!valid || busy) return
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      const res = await setupTable({
        table_no: Number(form.table_no),
        table_password: form.table_password,
      })
      setResult(res)
      setForm({ table_no: '', table_password: '' })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="tables">
      <div className="page-head"><h2>테이블 태블릿 설정</h2></div>
      <form className="card narrow" onSubmit={submit}>
        <p className="muted">
          태블릿마다 테이블 번호와 비밀번호를 1회 설정하면, 고객 화면이 자동 로그인으로 즉시 주문할 수 있습니다.
        </p>
        <label>
          테이블 번호
          <input type="number" min="1" step="1" value={form.table_no} onChange={set('table_no')} />
        </label>
        <label>
          테이블 비밀번호(4자 이상)
          <input type="password" value={form.table_password} onChange={set('table_password')} />
          {form.table_password && !pwOk && <span className="hint">4자 이상 입력하세요.</span>}
        </label>
        {error && <div className="error" role="alert">{error}</div>}
        {result && (
          <div className="success" role="status">
            테이블 {result.table_no}번 설정 완료 (ID {result.table_id?.slice(0, 8)}).
          </div>
        )}
        <button className="btn primary" type="submit" disabled={!valid || busy}>
          {busy ? '저장 중…' : '테이블 설정 저장'}
        </button>
      </form>
    </div>
  )
}
