import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { startSession as apiStartSession } from '../api/auth.js'
import { setSessionToken, setUnauthorizedHandler } from '../api/client.js'

// US-AUTH-05 / BR-FC02: the table session is persisted in localStorage so a
// tablet auto-logs-in on reload. On boot we hydrate the token into the API
// client; on any 401 we drop the session (BR-FC03).

const STORAGE_KEY = 'customer_session'
const SessionContext = createContext(null)

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function SessionProvider({ children }) {
  const [session, setSession] = useState(() => load())
  // `loading` covers the synchronous boot; kept for API symmetry with guards.
  const [loading] = useState(false)

  // Keep the API client's token in sync with session state.
  useEffect(() => {
    setSessionToken(session?.session_token || null)
  }, [session])

  const clear = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setSessionToken(null)
    setSession(null)
  }, [])

  // Register the global 401 handler once.
  useEffect(() => {
    setUnauthorizedHandler(() => clear())
    return () => setUnauthorizedHandler(null)
  }, [clear])

  const start = useCallback(async ({ storeCode, tableNo, tablePassword }) => {
    const data = await apiStartSession({ storeCode, tableNo, tablePassword })
    // Inject the token before any subsequent request; persist for auto-login.
    setSessionToken(data.session_token)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    setSession(data)
    return data
  }, [])

  return (
    <SessionContext.Provider value={{ session, loading, start, clear }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used within SessionProvider')
  return ctx
}
