import { useState } from 'react'
import { pageKeepingFirstItem, paginate, type PageSlice } from './pagination'

export interface Pager<T> extends PageSlice<T> {
  total: number
  pageSize: number
  pageSizes: readonly number[]
  goTo: (page: number) => void
  resize: (pageSize: number) => void
}

/**
 * Client-side pagination over a list that is already loaded.
 *
 * The page is clamped on every render, so a list that shrinks never leaves an empty page behind.
 */
export function usePagination<T>(items: readonly T[], pageSizes: readonly number[]): Pager<T> {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(pageSizes[0] ?? 25)
  const slice = paginate(items, page, pageSize)

  return {
    ...slice,
    total: items.length,
    pageSize,
    pageSizes,
    goTo: setPage,
    resize: (size) => {
      setPage(pageKeepingFirstItem(slice.page, pageSize, size))
      setPageSize(size)
    },
  }
}
