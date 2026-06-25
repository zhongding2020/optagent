import { useRef, useEffect, useCallback, useState } from 'react'
import type { WSEvent } from '../types/events'

export function useWebSocket(sessionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null)
  const [events, setEvents] = useState<WSEvent[]>([])
  const [connected, setConnected] = useState(false)

  const connect = useCallback(() => {
    if (!sessionId) return
    const ws = new WebSocket(`ws://localhost:8020/ws/sessions/${sessionId}`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      setTimeout(connect, 1000)
    }
    ws.onmessage = (e) => {
      const event = JSON.parse(e.data) as WSEvent
      setEvents((prev) => [...prev, event])
    }
  }, [sessionId])

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [connect])

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  const terminate = useCallback(() => send({ type: 'user:terminate' }), [send])
  const nextStep = useCallback(() => send({ type: 'user:next_step' }), [send])

  return { events, connected, send, terminate, nextStep }
}
