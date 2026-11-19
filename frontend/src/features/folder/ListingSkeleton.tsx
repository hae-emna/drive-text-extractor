import { IndeterminateBar, Skeleton } from '../../components/Skeleton'
import { formatElapsed } from '../../lib/format'
import { useElapsed } from '../../lib/useElapsed'

const NAME_WIDTHS = ['w-2/5', 'w-3/5', 'w-1/3', 'w-1/2', 'w-2/5']
const SHOW_TIMER_AFTER_MS = 3000
const EXPLAIN_AFTER_MS = 8000

/** Stands in for the file table while the link is listed. */
export function ListingSkeleton({ recursive }: { recursive: boolean }) {
  const elapsed = useElapsed(true)

  return (
    <div className="space-y-4">
      <IndeterminateBar label="Listing files" />
      <p className="flex flex-wrap items-baseline gap-x-2 text-sm text-zinc-600 dark:text-zinc-400">
        <span role="status">
          {recursive ? 'Reading the folder and its subfolders…' : 'Reading the link…'}
        </span>
        {elapsed >= SHOW_TIMER_AFTER_MS && (
          // Visual only: announcing a ticking timer every second would drown screen readers.
          <span aria-hidden="true" className="text-xs text-zinc-500 tabular-nums">
            {formatElapsed(elapsed)}
          </span>
        )}
      </p>
      {elapsed >= EXPLAIN_AFTER_MS && (
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          Large folders and deep subfolders take longer to list.
        </p>
      )}

      <div
        aria-hidden="true"
        className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800"
      >
        <div className="flex items-center gap-4 bg-zinc-50 px-3 py-2.5 dark:bg-zinc-950">
          <Skeleton className="size-4" />
          <Skeleton className="h-3 w-16" />
        </div>
        <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {NAME_WIDTHS.map((width, index) => (
            <li key={index} className="flex items-center gap-4 px-3 py-3">
              <Skeleton className="size-4 shrink-0" />
              <Skeleton className={`h-3.5 ${width}`} />
              <Skeleton className="ml-auto h-3 w-10" />
              <Skeleton className="h-3 w-14" />
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
