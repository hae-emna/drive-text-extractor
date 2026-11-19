import type { SkippedFile } from '../../api/types'
import { plural } from '../../lib/format'

export function SkippedFiles({ skipped }: { skipped: SkippedFile[] }) {
  if (skipped.length === 0) return null
  return (
    <details className="rounded-lg border border-zinc-200 px-4 py-3 text-sm dark:border-zinc-800">
      <summary className="cursor-pointer text-zinc-600 dark:text-zinc-400">
        {plural(skipped.length, 'item')} not offered for extraction
      </summary>
      <ul className="mt-3 space-y-2">
        {skipped.map((item) => (
          <li key={`${item.name}-${item.mime_type}`} className="flex flex-col sm:flex-row sm:gap-3">
            <span className="font-medium sm:w-1/3 sm:truncate" title={item.name}>
              {item.name}
            </span>
            <span className="text-zinc-600 dark:text-zinc-400">{item.reason}</span>
          </li>
        ))}
      </ul>
    </details>
  )
}
