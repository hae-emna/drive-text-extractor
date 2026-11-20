import { useEffect, useState } from 'react'
import { MS_PER_SECOND } from './format'

/** Milliseconds since the component mounted, refreshed every `intervalMs` while `running`. */
export function useElapsed(running: boolean, intervalMs = MS_PER_SECOND): number {
  const [start] = useState(() => Date.now())
  const [now, setNow] = useState(start)

  useEffect(() => {
    if (!running) return
    const timer = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(timer)
  }, [running, intervalMs])

  return now - start
}
