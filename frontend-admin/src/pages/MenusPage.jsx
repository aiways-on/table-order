import { useEffect, useState } from 'react'
import { listMenus, createMenu, updateMenu, deleteMenu, reorderMenus } from '../api/menus.js'

const won = (n) => `${(n ?? 0).toLocaleString('ko-KR')}원`
const EMPTY = { name: '', price: '', category: '', description: '', image_url: '' }

// US-MENU-04~07. BR-FA11/BR-FA12/BR-FA13.
export default function MenusPage() {
  const [menus, setMenus] = useState([])
  const [form, setForm] = useState(EMPTY)
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = async () => {
    try {
      setMenus((await listMenus()) || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }
  useEffect(() => {
    load()
  }, [])

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  // BR-FA11 — mirror server validation.
  const priceNum = Number(form.price)
  const urlOk =
    !form.image_url.trim() || /^https?:\/\//.test(form.image_url.trim())
  const valid =
    form.name.trim() &&
    form.category.trim() &&
    form.price !== '' &&
    Number.isInteger(priceNum) &&
    priceNum >= 0 &&
    urlOk

  const resetForm = () => {
    setForm(EMPTY)
    setEditingId(null)
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!valid || busy) return
    setBusy(true)
    setError(null)
    const payload = {
      name: form.name.trim(),
      price: priceNum,
      category: form.category.trim(),
      description: form.description.trim() || null,
      image_url: form.image_url.trim() || null,
    }
    try {
      if (editingId) await updateMenu(editingId, payload)
      else await createMenu(payload)
      resetForm()
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const startEdit = (m) => {
    setEditingId(m.id)
    setForm({
      name: m.name || '',
      price: String(m.price ?? ''),
      category: m.category || '',
      description: m.description || '',
      image_url: m.image_url || '',
    })
  }

  const remove = async (m) => {
    if (!window.confirm(`'${m.name}' 메뉴를 삭제할까요?`)) return
    try {
      await deleteMenu(m.id)
      if (editingId === m.id) resetForm()
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  // BR-FA12 — move within the list, then persist full permutation.
  const move = async (idx, dir) => {
    const j = idx + dir
    if (j < 0 || j >= menus.length) return
    const next = [...menus]
    ;[next[idx], next[j]] = [next[j], next[idx]]
    setMenus(next) // optimistic
    try {
      await reorderMenus(next.map((m) => m.id))
    } catch (err) {
      setError(err.message)
      load() // revert to server truth
    }
  }

  return (
    <div className="menus">
      <div className="page-head"><h2>메뉴 관리</h2></div>
      {error && <div className="error" role="alert">{error}</div>}

      <div className="split">
        <div className="list card">
          {menus.length === 0 && <div className="muted empty">등록된 메뉴가 없습니다.</div>}
          {menus.map((m, i) => (
            <div key={m.id} className={`menu-row ${editingId === m.id ? 'sel' : ''}`}>
              <div className="menu-order">
                <button className="btn tiny" disabled={i === 0} onClick={() => move(i, -1)}>▲</button>
                <button className="btn tiny" disabled={i === menus.length - 1} onClick={() => move(i, 1)}>▼</button>
              </div>
              <div className="menu-main">
                <div className="menu-name">{m.name} <span className="tag">{m.category}</span></div>
                {m.description && <div className="muted small">{m.description}</div>}
              </div>
              <div className="menu-price">{won(m.price)}</div>
              <div className="menu-actions">
                <button className="btn tiny" onClick={() => startEdit(m)}>수정</button>
                <button className="btn tiny danger" onClick={() => remove(m)}>삭제</button>
              </div>
            </div>
          ))}
        </div>

        <form className="card menu-form" onSubmit={submit}>
          <h3>{editingId ? '메뉴 수정' : '메뉴 등록'}</h3>
          <label>메뉴명<input value={form.name} onChange={set('name')} maxLength={100} /></label>
          <label>가격(원)<input type="number" min="0" step="1" value={form.price} onChange={set('price')} /></label>
          <label>카테고리<input value={form.category} onChange={set('category')} maxLength={50} /></label>
          <label>설명<textarea value={form.description} onChange={set('description')} maxLength={500} /></label>
          <label>
            이미지 URL
            <input value={form.image_url} onChange={set('image_url')} placeholder="https://…" />
            {!urlOk && <span className="hint">http:// 또는 https:// 로 시작해야 합니다.</span>}
          </label>
          <div className="actions">
            <button className="btn primary" type="submit" disabled={!valid || busy}>
              {busy ? '저장 중…' : editingId ? '수정 저장' : '등록'}
            </button>
            {editingId && <button className="btn ghost" type="button" onClick={resetForm}>취소</button>}
          </div>
        </form>
      </div>
    </div>
  )
}
