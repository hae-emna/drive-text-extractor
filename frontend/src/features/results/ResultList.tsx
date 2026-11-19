import { useRef } from 'react'
import { api } from '../../api/client'
import type { Job } from '../../api/types'
import { Button } from '../../components/Button'
import { Pagination } from '../../components/Pagination'
import { revealTop } from '../../lib/dom'
import { usePagination } from '../../lib/usePagination'
import { ResultCard } from './ResultCard'

const PAGE_SIZES = [10, 25, 50]

interface ResultListProps {
  job: Job
  onSelectFailed: (fileIds: string[]) => void
}

export function ResultList({ job, onSelectFailed }: ResultListProps) {
  const finished = job.status === 'finished'
  const failedIds = job.files.filter((r) => r.status === 'failed').map((r) => r.file.id)
  const pager = usePagination(job.files, PAGE_SIZES)
  const topRef = useRef<HTMLDivElement>(null)

  return (
    <div ref={topRef} className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {finished ? (
          <a
            href={api.exportUrl(job.id)}
            download
            className="inline-flex items-center rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lime-500 dark:bg-lime-300 dark:text-zinc-950 dark:hover:bg-lime-200"
          >
            Export JSON
          </a>
        ) : (
          <Button disabled title="Available when the batch has finished">
            Export JSON
          </Button>
        )}
        {finished && failedIds.length > 0 && (
          <Button variant="secondary" onClick={() => onSelectFailed(failedIds)}>
            Select failed files to retry
          </Button>
        )}
      </div>
      {pager.items.map((result) => (
        <ResultCard key={result.file.id} result={result} />
      ))}
      <Pagination
        label="Result pages"
        noun="result"
        pager={pager}
        onNavigate={() => revealTop(topRef.current)}
      />
    </div>
  )
}
