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
  | { status: 'loading'; request: ListingRequest }
  | { status: 'error'; error: ApiError }
  | { status: 'loaded'; listing: FolderListing; request: ListingRequest }

export function useFolderListing() {
  const [state, setState] = useState<ListingState>({ status: 'idle' })
  // Only the latest request may update the state: an older, slower answer is ignored.
  const latest = useRef(0)

  /** Resolves with the listing, or null if it failed or a newer request replaced it. */
  const load = useCallback(
    async (link: string, recursive: boolean): Promise<FolderListing | null> => {
      const requestNumber = ++latest.current
      setState({ status: 'loading', request: { link, recursive } })
      try {
        const listing = await api.listFiles(link, recursive)
        if (requestNumber !== latest.current) return null
        setState({ status: 'loaded', listing, request: { link, recursive } })
        return listing
      } catch (error) {
        if (requestNumber === latest.current)
          setState({ status: 'error', error: toApiError(error) })
        return null
      }
    },
    [],
  )

  return { state, load }
}
