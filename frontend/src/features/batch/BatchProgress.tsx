import type { Job } from '../../api/types'
import { Button } from '../../components/Button'
import { plural } from '../../lib/format'

interface BatchProgressProps {
  job: Job
  onCancel: () => void
}

export function BatchProgress({ job, onCancel }: BatchProgressProps) {
  const { total, done, failed, cancelled } = job.summary
  const finished = done + failed + cancelled
  const percent = total === 0 ? 100 : Math.round((finished / total) * 100)
  const running = job.status === 'running'

  const details = [
    `${done} done`,
    failed > 0 ? `${failed} failed` : null,
    cancelled > 0 ? `${cancelled} cancelled` : null,
  ].filter(Boolean)

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
        <p aria-live="polite">
          <span className="font-medium">
            {running
              ? `Processing… ${finished} of ${plural(total, 'file')}`
              : `Finished: ${plural(total, 'file')}`}
          </span>
          <span className="text-zinc-600 dark:text-zinc-400"> · {details.join(' · ')}</span>
        </p>
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
        className="h-2 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800"
      >
        <div
          className={`h-full rounded-full transition-[width] duration-500 ${failed > 0 ? 'bg-amber-500' : 'bg-lime-500'}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}
