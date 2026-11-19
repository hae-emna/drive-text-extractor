// Pure pagination helpers. Pages are 1-based, as they are shown to the user.

export interface PageSlice<T> {
  /** The items of the current page. */
  items: T[]
  /** The current page, clamped to the pages that exist. */
  page: number
  /** At least 1, so an empty list still has one (empty) page. */
  pageCount: number
  /** 1-based position of the first item shown, or 0 when there is nothing to show. */
  first: number
  /** 1-based position of the last item shown, or 0 when there is nothing to show. */
  last: number
}

export function paginate<T>(items: readonly T[], page: number, pageSize: number): PageSlice<T> {
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize))
  const current = Math.min(Math.max(1, Math.trunc(page)), pageCount)
  const offset = (current - 1) * pageSize
  const slice = items.slice(offset, offset + pageSize)
  return {
    items: slice,
    page: current,
    pageCount,
    first: slice.length > 0 ? offset + 1 : 0,
    last: offset + slice.length,
  }
}

/** The page that keeps the first item of the current page visible after a page-size change. */
export function pageKeepingFirstItem(page: number, oldSize: number, newSize: number): number {
  return Math.floor(((page - 1) * oldSize) / newSize) + 1
}

export type PageLink = number | 'gap'

/**
 * Page numbers worth a button: the first and last pages, the current page and its neighbours.
 * Runs of skipped pages become a gap, except a single skipped page, which is cheaper to show
 * than an ellipsis standing in for it.
 */
export function pageLinks(current: number, pageCount: number, siblings = 1): PageLink[] {
  const shown = new Set([1, pageCount])
  for (let page = current - siblings; page <= current + siblings; page += 1) {
    if (page >= 1 && page <= pageCount) shown.add(page)
  }
  const sorted = [...shown].sort((a, b) => a - b)

  const links: PageLink[] = []
  let previous = 0
  for (const page of sorted) {
    if (page - previous === 2) links.push(page - 1)
    else if (page - previous > 2) links.push('gap')
    links.push(page)
    previous = page
  }
  return links
}
