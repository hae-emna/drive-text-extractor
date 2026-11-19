import type { FileStatus } from '../../api/types'
import { Spinner } from '../../components/Spinner'

const STYLES: Record<FileStatus, string> = {
  pending: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
  processing: 'bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-200',
  done: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200',
  cancelled: 'bg-zinc-100 text-zinc-500 line-through dark:bg-zinc-800 dark:text-zinc-400',
}

export function StatusBadge({ status }: { status: FileStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}
    >
      {status === 'processing' && <Spinner className="size-3" />}
      {status}
    </span>
  )
}
