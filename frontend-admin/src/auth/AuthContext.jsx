import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react'
import * as authApi from '../api/auth.js'
import { setUnauthorizedHandler } from '../api/client.js'

// The session cookie is HttpOnly (not readable in JS). We persist store_id in
// localStorage so the login UI survives refresh (US-AUTH-02 / BR-FA02); the
// server cookie remains the real source of truth. Any 401 clears state and the
// ProtectedRoute sends the user back to /login (BR-FA03).
const STORAGE_KEY = 'admin_store'
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) setAuth(JSON.parse(raw))
    } catch {
      /* ignore malformed storage */
    }
    setLoading(false)
  }, [])

  const clear = useCallback(() => {
    setAuth(null)
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      /* ignore */
    }
  }, [])

  // Register global 401 handler once.
  useEffect(() => {
    setUnauthorizedHandler(() => clear())
    return () => setUnauthorizedHandler(null)
  }, [clear])

  const login = useCallback(async (creds) => {
    const res = await authApi.login(creds) // { store_id, role }
    const next = { store_id: res.store_id, role: res.role || 'admin' }
    setAuth(next)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    } catch {
      /* ignore */
    }
    return next
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      /* even if the call fails, drop local state */
    }
    clear()
  }, [clear])

  const value = useMemo(
    () => ({ auth, loading, isAuthenticated: !!auth, login, logout }),
    [auth, loading, login, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
