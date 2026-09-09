import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { SessionProvider, useSession } from './SessionContext.jsx'

const wrapper = ({ children }) => <SessionProvider>{children}</SessionProvider>
const STORAGE_KEY = 'customer_session'

describe('SessionContext (US-AUTH-05 / BR-FC02,03)', () => {
  beforeEach(() => {
    localStorage.clear()
    global.fetch = vi.fn()
  })
  afterEach(() => vi.restoreAllMocks())

  it('auto-logs-in from a stored session on boot', () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ session_id: 's1', session_token: 'tok', store_id: 'st1', table_id: 't1' })
    )
    const { result } = renderHook(() => useSession(), { wrapper })
    expect(result.current.session?.session_token).toBe('tok')
  })

  it('starts a session and persists it for the next reload', async () => {
    global.fetch.mockResolvedValue(
      new Response(
        JSON.stringify({ session_id: 's1', session_token: 'tok', store_id: 'st1', table_id: 't1' }),
        { status: 200 }
      )
    )
    const { result } = renderHook(() => useSession(), { wrapper })
    await act(async () => {
      await result.current.start({ storeCode: 'CAFE01', tableNo: 1, tablePassword: '1234' })
    })
    expect(result.current.session?.session_id).toBe('s1')
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY)).session_token).toBe('tok')
  })

  it('clear() drops the stored session', async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ session_id: 's1', session_token: 'tok', store_id: 'st1', table_id: 't1' })
    )
    const { result } = renderHook(() => useSession(), { wrapper })
    act(() => result.current.clear())
    await waitFor(() => expect(result.current.session).toBeNull())
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
  })
})
