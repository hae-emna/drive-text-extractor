import type { FileStatus, Job } from '../../api/types'
import { Button } from '../../components/Button'
import { estimateRemainingMs, formatElapsed, formatRemaining, plural } from '../../lib/format'
import { useElapsed } from '../../lib/useElapsed'

interface BatchProgressProps {
  job: Job
  onCancel: () => void
}

interface Segment {
  status: FileStatus
  label: string
  bar: string
  dot: string
}

// Finished work first, then work in progress; files still waiting are the empty track.
const SEGMENTS: Segment[] = [
  { status: 'done', label: 'done', bar: 'bg-emerald-500', dot: 'bg-emerald-500' },
  { status: 'failed', label: 'failed', bar: 'bg-red-500', dot: 'bg-red-500' },
  {
    status: 'cancelled',
    label: 'cancelled',
    bar: 'bg-zinc-400 dark:bg-zinc-500',
    dot: 'bg-zinc-400 dark:bg-zinc-500',
  },
  {
    status: 'processing',
    label: 'processing',
    bar: 'bg-sky-500 stripes animate-stripes motion-reduce:animate-none',
    dot: 'bg-sky-500',
  },
]

const MAX_NAMES = 3

export function BatchProgress({ job, onCancel }: BatchProgressProps) {
  const { summary } = job
  const finished = summary.done + summary.failed + summary.cancelled
  const percent = summary.total === 0 ? 100 : Math.round((finished / summary.total) * 100)
  const running = job.status === 'running'

  const elapsed = useElapsed(running)
  const duration = running ? elapsed : (serverDuration(job) ?? elapsed)
  const remaining = running ? estimateRemainingMs(elapsed, finished, summary.total) : null
  const reading = job.files.filter((r) => r.status === 'processing').map((r) => r.file.name)

  return (
    <div className="space-y-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-0.5">
          <p className="text-sm font-medium" aria-live="polite">
            {running
              ? job.cancel_requested
                ? `Cancelling… ${finished} of ${plural(summary.total, 'file')} finished`
                : `Processing… ${finished} of ${plural(summary.total, 'file')}`
              : `Finished: ${plural(summary.total, 'file')}`}
          </p>
          <p className="text-xs text-zinc-500 tabular-nums dark:text-zinc-400">
            {running ? `${formatElapsed(duration)} elapsed` : `in ${formatElapsed(duration)}`}
            {remaining !== null && !job.cancel_requested && ` · ${formatRemaining(remaining)}`}
          </p>
        </div>
        {running && (
          <Button variant="secondary" onClick={onCancel} disabled={job.cancel_requested}>
            {job.cancel_requested ? 'Cancelling…' : 'Cancel'}
          </Button>
        )}
      </div>

      <div
        role="progressbar"
        aria-label="Batch progress"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-valuetext={`${finished} of ${plural(summary.total, 'file')} finished`}
        className="flex h-2.5 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800"
      >
        {SEGMENTS.map(({ status, bar }) => {
          const count = summary[status]
          if (count === 0) return null
          return (
            <div
              key={status}
              className={`h-full transition-[width] duration-500 ease-out motion-reduce:transition-none ${bar}`}
              style={{ width: `${(count / summary.total) * 100}%` }}
            />
          )
        })}
      </div>

      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-600 dark:text-zinc-400">
        {SEGMENTS.map(({ status, label, dot }) =>
          summary[status] > 0 || status === 'done' ? (
            <LegendItem key={status} dot={dot} text={`${summary[status]} ${label}`} />
          ) : null,
        )}
        {summary.pending > 0 && (
          <LegendItem dot="bg-zinc-300 dark:bg-zinc-700" text={`${summary.pending} waiting`} />
        )}
      </ul>

      {running && reading.length > 0 && (
        <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
          Reading {reading.slice(0, MAX_NAMES).join(', ')}
          {reading.length > MAX_NAMES && ` and ${reading.length - MAX_NAMES} more`}
        </p>
      )}
    </div>
  )
}

function LegendItem({ dot, text }: { dot: string; text: string }) {
  return (
    <li className="inline-flex items-center gap-1.5 tabular-nums">
      {/* The dot repeats the bar colour; the text alone carries the meaning. */}
      <span aria-hidden="true" className={`size-2 rounded-full ${dot}`} />
      {text}
    </li>
  )
}

/** How long a finished job took, by the server's clock. */
function serverDuration(job: Job): number | null {
  if (!job.finished_at) return null
  const ms = Date.parse(job.finished_at) - Date.parse(job.created_at)
  return Number.isFinite(ms) && ms >= 0 ? ms : null
}
