import { describe, expect, it } from 'vitest'
import { pageKeepingFirstItem, pageLinks, paginate } from './pagination'

const ITEMS = Array.from({ length: 23 }, (_, index) => index + 1)

describe('paginate', () => {
  it('returns the items of the requested page and their positions', () => {
    expect(paginate(ITEMS, 2, 10)).toEqual({
      items: [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
      page: 2,
      pageCount: 3,
      first: 11,
      last: 20,
    })
  })

  it('returns a short last page', () => {
    const slice = paginate(ITEMS, 3, 10)

    expect(slice.items).toEqual([21, 22, 23])
    expect([slice.first, slice.last]).toEqual([21, 23])
  })

  it.each([
    [0, 1],
    [-4, 1],
    [99, 3],
  ])('clamps page %i to page %i', (requested, expected) => {
    expect(paginate(ITEMS, requested, 10).page).toBe(expected)
  })

  it('has one empty page when there is nothing to show', () => {
    expect(paginate([], 1, 10)).toEqual({ items: [], page: 1, pageCount: 1, first: 0, last: 0 })
  })
})

describe('pageKeepingFirstItem', () => {
  it('keeps the first visible item on screen when the page size changes', () => {
    // Page 3 of 10 starts at item 21: with 25 per page, item 21 is on page 1.
    expect(pageKeepingFirstItem(3, 10, 25)).toBe(1)
    // Page 2 of 25 starts at item 26: with 10 per page, item 26 is on page 3.
    expect(pageKeepingFirstItem(2, 25, 10)).toBe(3)
  })
})

describe('pageLinks', () => {
  it('lists every page when there are few', () => {
    expect(pageLinks(1, 1)).toEqual([1])
    expect(pageLinks(2, 5)).toEqual([1, 2, 3, 4, 5])
  })

  it('collapses long runs into gaps around the current page', () => {
    expect(pageLinks(10, 20)).toEqual([1, 'gap', 9, 10, 11, 'gap', 20])
  })

  it('shows a single skipped page instead of a gap', () => {
    expect(pageLinks(4, 20)).toEqual([1, 2, 3, 4, 5, 'gap', 20])
  })

  it('keeps the edges compact', () => {
    expect(pageLinks(1, 20)).toEqual([1, 2, 'gap', 20])
    expect(pageLinks(20, 20)).toEqual([1, 'gap', 19, 20])
  })
})
