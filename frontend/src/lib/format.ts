const TYPE_LABELS: Record<string, string> = {
  'application/pdf': 'PDF',
  'image/png': 'PNG',
  'image/jpeg': 'JPEG',
}

export function fileTypeLabel(mimeType: string): string {
  return TYPE_LABELS[mimeType] ?? (mimeType.split('/').pop() ?? mimeType).toUpperCase()
}

export function formatBytes(bytes: number | null): string {
  if (bytes === null) return '—'
  if (bytes < 1000) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let value = bytes / 1000
  let unit = 0
  while (value >= 1000 && unit < units.length - 1) {
    value /= 1000
    unit += 1
  }
  return `${value.toFixed(value < 10 ? 1 : 0)} ${units[unit]}`
}

export function formatDuration(ms: number | null): string {
  if (ms === null) return '—'
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`
}

export function plural(count: number, singular: string, pluralForm = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : pluralForm}`
}

/** A running time: "8 s", "2 min 05 s". */
export function formatElapsed(ms: number): string {
  const seconds = Math.max(0, Math.floor(ms / 1000))
  if (seconds < 60) return `${seconds} s`
  const rest = String(seconds % 60).padStart(2, '0')
  return `${Math.floor(seconds / 60)} min ${rest} s`
}

/**
 * Time left at the pace so far, or null until there is a pace to go by.
 * Files differ a lot (a one-page PDF against a scanned 50-page one), so this is a rough guide.
 */
export function estimateRemainingMs(elapsedMs: number, finished: number, total: number) {
  if (finished === 0 || finished >= total || elapsedMs < 1000) return null
  return (elapsedMs / finished) * (total - finished)
}

/** "a few seconds left", "about 40 s left", "about 3 min left". */
export function formatRemaining(ms: number): string {
  const seconds = ms / 1000
  if (seconds < 10) return 'a few seconds left'
  const roundedSeconds = Math.round(seconds / 5) * 5
  if (roundedSeconds < 60) return `about ${roundedSeconds} s left`
  return `about ${Math.max(1, Math.round(seconds / 60))} min left`
}
