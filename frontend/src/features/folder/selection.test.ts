import { describe, expect, it } from 'vitest'
import { selectedInOrder, selectionState, toggle, toggleAll } from './selection'

const ALL = ['a', 'b', 'c']

describe('selection', () => {
  it('toggles one id without mutating the original set', () => {
    const original = new Set(['a'])

    expect([...toggle(original, 'b')]).toEqual(['a', 'b'])
    expect([...toggle(original, 'a')]).toEqual([])
    expect([...original]).toEqual(['a'])
  })

  it('selects everything unless everything is already selected', () => {
    expect([...toggleAll(new Set(), ALL)]).toEqual(ALL)
    expect([...toggleAll(new Set(['b']), ALL)].sort()).toEqual(ALL)
    expect([...toggleAll(new Set(ALL), ALL)]).toEqual([])
  })

  it('leaves ids outside the toggled group alone', () => {
    const otherPage = new Set(['x', 'a'])

    expect([...toggleAll(otherPage, ALL)].sort()).toEqual(['a', 'b', 'c', 'x'])
    expect([...toggleAll(new Set(['x', ...ALL]), ALL)]).toEqual(['x'])
  })

  it.each([
    [[], 'none'],
    [['b'], 'some'],
    [ALL, 'all'],
    [['stale-id'], 'none'],
  ])('reports %j as %s', (ids, expected) => {
    expect(selectionState(new Set(ids), ALL)).toBe(expected)
  })

  it('returns selected ids in list order, dropping ids no longer listed', () => {
    expect(selectedInOrder(new Set(['c', 'gone', 'a']), ALL)).toEqual(['a', 'c'])
  })
})
