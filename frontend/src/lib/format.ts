const TYPE_LABELS: Record<string, string> = {
  'application/pdf': 'PDF',
  'image/png': 'PNG',
  'image/jpeg': 'JPEG',
  'text/plain': 'TXT',
  'inode/directory': 'Folder',
  'application/vnd.google-apps.folder': 'Folder',
  'application/vnd.google-apps.shortcut': 'Shortcut',
  'application/vnd.google-apps.document': 'Google Doc',
  'application/vnd.google-apps.spreadsheet': 'Google Sheet',
  'application/vnd.google-apps.presentation': 'Google Slides',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
  'application/octet-stream': 'File',
}

const FOLDER_TYPES = new Set(['inode/directory', 'application/vnd.google-apps.folder'])

/** Decimal units, as Google Drive shows sizes. */
const BYTES_PER_KB = 1000
const SIZE_UNITS = ['KB', 'MB', 'GB']
/** Values below this get one decimal: "2.5 MB", but "25 MB". */
const ONE_DECIMAL_BELOW = 10

export const MS_PER_SECOND = 1000
const SECONDS_PER_MINUTE = 60
/** Below this, a countdown is not worth a number. */
const FEW_SECONDS = 10
/** Estimates are rounded to this step so they do not flicker on every tick. */
const ESTIMATE_STEP_SECONDS = 5

/** "PDF", "Google Doc"; otherwise the last part of the subtype: "image/svg+xml" gives "SVG". */
export function fileTypeLabel(mimeType: string): string {
  const known = TYPE_LABELS[mimeType]
  if (known) return known
  const subtype = mimeType.split('/').pop() ?? mimeType
  return (subtype.split('+')[0]?.split('.').pop() || subtype).toUpperCase()
}

export function isFolderType(mimeType: string): boolean {
  return FOLDER_TYPES.has(mimeType)
}

export function formatBytes(bytes: number | null): string {
  if (bytes === null) return '—'
  if (bytes < BYTES_PER_KB) return `${bytes} B`
  let value = bytes / BYTES_PER_KB
  let unitIndex = 0
  while (value >= BYTES_PER_KB && unitIndex < SIZE_UNITS.length - 1) {
    value /= BYTES_PER_KB
    unitIndex += 1
  }
  return `${value.toFixed(value < ONE_DECIMAL_BELOW ? 1 : 0)} ${SIZE_UNITS[unitIndex]}`
}

export function formatDuration(ms: number | null): string {
  if (ms === null) return '—'
  return ms < MS_PER_SECOND ? `${ms} ms` : `${(ms / MS_PER_SECOND).toFixed(1)} s`
}

export function plural(count: number, singular: string, pluralForm = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : pluralForm}`
}

/** A running time: "8 s", "2 min 05 s". */
export function formatElapsed(ms: number): string {
  const seconds = Math.max(0, Math.floor(ms / MS_PER_SECOND))
  if (seconds < SECONDS_PER_MINUTE) return `${seconds} s`
  const restSeconds = String(seconds % SECONDS_PER_MINUTE).padStart(2, '0')
  return `${Math.floor(seconds / SECONDS_PER_MINUTE)} min ${restSeconds} s`
}

/**
 * Time left at the pace so far, or null until there is a pace to go by.
 * Files differ a lot (a one-page PDF against a scanned 50-page one), so this is a rough guide.
 */
export function estimateRemainingMs(elapsedMs: number, finished: number, total: number) {
  if (finished === 0 || finished >= total || elapsedMs < MS_PER_SECOND) return null
  return (elapsedMs / finished) * (total - finished)
}

/** "a few seconds left", "about 40 s left", "about 3 min left". */
export function formatRemaining(ms: number): string {
  const seconds = ms / MS_PER_SECOND
  if (seconds < FEW_SECONDS) return 'a few seconds left'
  const roundedSeconds = Math.round(seconds / ESTIMATE_STEP_SECONDS) * ESTIMATE_STEP_SECONDS
  if (roundedSeconds < SECONDS_PER_MINUTE) return `about ${roundedSeconds} s left`
  return `about ${Math.max(1, Math.round(seconds / SECONDS_PER_MINUTE))} min left`
}
