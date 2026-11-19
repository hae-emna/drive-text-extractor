// Pure selection helpers: easy to test, and components stay free of set juggling.

export type SelectionState = 'none' | 'some' | 'all'

export function toggle(selected: ReadonlySet<string>, id: string): Set<string> {
  const next = new Set(selected)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  return next
}

/**
 * Select every id of a group (e.g. one page), or unselect them all when they all are selected.
 * Ids outside the group keep their state.
 */
export function toggleAll(selected: ReadonlySet<string>, groupIds: readonly string[]): Set<string> {
  const next = new Set(selected)
  if (selectionState(selected, groupIds) === 'all') for (const id of groupIds) next.delete(id)
  else for (const id of groupIds) next.add(id)
  return next
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
