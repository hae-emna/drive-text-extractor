import { useCallback, useRef, useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { FolderListing } from '../../api/types'
import { toApiError } from '../../lib/errors'

export interface ListingRequest {
  link: string
  recursive: boolean
}

export type ListingState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; error: ApiError }
  | { status: 'loaded'; listing: FolderListing; request: ListingRequest }

export function useFolderListing() {
  const [state, setState] = useState<ListingState>({ status: 'idle' })
  // Only the latest request may update the state: an older, slower answer is ignored.
  const latest = useRef(0)

  const load = useCallback(async (link: string, recursive: boolean) => {
    const requestNumber = ++latest.current
    setState({ status: 'loading' })
    try {
      const listing = await api.listFolder(link, recursive)
      if (requestNumber === latest.current) {
        setState({ status: 'loaded', listing, request: { link, recursive } })
      }
    } catch (error) {
      if (requestNumber === latest.current) setState({ status: 'error', error: toApiError(error) })
    }
  }, [])

  return { state, load }
}
