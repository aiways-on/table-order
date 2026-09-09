import { useEffect, useRef, useState } from 'react'

// US-ORDER-09 realtime + RES-10 resiliency.
// Connects to the admin store SSE (`/api/orders/stream`, JWT cookie). The
// backend sends unnamed `data: {json}` frames, so we parse in `onmessage` and
// dispatch by `type` (order_created | order_status | order_deleted |
// session_closed). EventSource auto-reconnects; on each (re)connect we call
// `onResync` so the caller re-fetches the full store list and heals any gap.
export function useOrderStream({ onEvent, onResync }) {
  const [connected, setConnected] = useState(false)
  const onEventRef = useRef(onEvent)
  const onResyncRef = useRef(onResync)
  onEventRef.current = onEvent
  onResyncRef.current = onResync

  useEffect(() => {
    // withCredentials so the HttpOnly cookie rides along.
    const es = new EventSource('/api/orders/stream', { withCredentials: true })

    es.onopen = () => {
      setConnected(true)
      // Heal any events missed while disconnected (BR-FA10).
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
      // Browser will retry automatically; reflect the transient drop in UI.
      setConnected(false)
    }

    return () => es.close()
  }, [])

  return { connected }
}
