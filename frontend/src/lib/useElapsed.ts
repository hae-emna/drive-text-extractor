import { useEffect, useState } from 'react'

/** Milliseconds since the component mounted, refreshed every `intervalMs` while `running`. */
export function useElapsed(running: boolean, intervalMs = 1000): number {
  const [start] = useState(() => Date.now())
  const [now, setNow] = useState(start)

  useEffect(() => {
    if (!running) return
    const timer = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(timer)
  }, [running, intervalMs])

  return now - start
}
