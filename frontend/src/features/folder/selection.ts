// Pure selection helpers: easy to test, and components stay free of set juggling.

export type SelectionState = 'none' | 'some' | 'all'

export function toggle(selected: ReadonlySet<string>, id: string): Set<string> {
  const next = new Set(selected)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  return next
}

/** Select everything, or clear the selection when everything is already selected. */
export function toggleAll(selected: ReadonlySet<string>, allIds: readonly string[]): Set<string> {
  return selectionState(selected, allIds) === 'all' ? new Set() : new Set(allIds)
}

export function selectionState(
  selected: ReadonlySet<string>,
  allIds: readonly string[],
): SelectionState {
  const count = allIds.filter((id) => selected.has(id)).length
  if (count === 0) return 'none'
  return count === allIds.length ? 'all' : 'some'
}

/** Keep only ids that still exist, in list order (used when submitting a selection). */
export function selectedInOrder(
  selected: ReadonlySet<string>,
  allIds: readonly string[],
): string[] {
  return allIds.filter((id) => selected.has(id))
}
