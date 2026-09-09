import { useEffect, useRef, useState } from 'react'

// US-ORDER-08 realtime + RES-10 resiliency.
// Connects to the customer session SSE. EventSource cannot set headers, so the
// session token rides as ?token= (TLS-only in prod; local HTTP allowed). The
// backend sends unnamed `data: {json}` frames, so we parse in onmessage and
// dispatch by `type` (order_created | order_status | order_deleted |
// session_closed). EventSource auto-reconnects; on each (re)connect we call
// onResync so the caller re-fetches the full list and heals any gap. [BR-FC12][BR-FC14]
export function useOrderStream({ token, onEvent, onResync }) {
  const [connected, setConnected] = useState(false)
  const onEventRef = useRef(onEvent)
  const onResyncRef = useRef(onResync)
  onEventRef.current = onEvent
  onResyncRef.current = onResync

  useEffect(() => {
    if (!token) return undefined

    const url = `/api/orders/session/stream?token=${encodeURIComponent(token)}`
    const es = new EventSource(url)

    es.onopen = () => {
      setConnected(true)
      if (onResyncRef.current) onResyncRef.current()
    }
    es.onmessage = (ev) => {
      if (!ev.data) return
      try {
        const data = JSON.parse(ev.data)
        if (onEventRef.current) onEventRef.current(data)
      } catch {
        /* ignore keep-alive/comment frames */
      }
    }
    es.onerror = () => {
      // Browser retries automatically; reflect the transient drop.
      setConnected(false)
    }

    return () => es.close()
  }, [token])

  return { connected }
}
