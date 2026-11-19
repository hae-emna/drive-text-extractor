import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { Health } from '../../api/types'

/** Server capabilities (installed OCR languages). ``null`` until known or if unreachable. */
export function useHealth(): Health | null {
  const [health, setHealth] = useState<Health | null>(null)

  useEffect(() => {
    let active = true
    api
      .health()
      .then((value) => active && setHealth(value))
      .catch(() => {
        // The listing call will surface connectivity problems with a proper message.
      })
    return () => {
      active = false
    }
  }, [])

  return health
}
