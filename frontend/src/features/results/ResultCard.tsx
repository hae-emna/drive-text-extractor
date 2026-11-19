import type { FileResult, FileStatus } from '../../api/types'
import { Skeleton } from '../../components/Skeleton'
import { Spinner } from '../../components/Spinner'
import { formatDuration, plural } from '../../lib/format'
import { StatusBadge } from '../batch/StatusBadge'
import { CopyButton } from './CopyButton'
import { ExtractedText } from './ExtractedText'
import { MethodBadge } from './MethodBadge'

const BORDERS: Record<FileStatus, string> = {
  pending: 'border-dashed border-zinc-300 dark:border-zinc-700',
  processing: 'border-sky-200 dark:border-sky-900',
  done: 'border-zinc-200 dark:border-zinc-800',
  failed: 'border-red-200 dark:border-red-900',
  cancelled: 'border-zinc-200 dark:border-zinc-800',
}

export function ResultCard({ result }: { result: FileResult }) {
  const { file, status, error } = result
  return (
    <article
      aria-label={file.path}
      aria-busy={status === 'pending' || status === 'processing'}
      className={`space-y-3 rounded-lg border p-4 transition-colors ${BORDERS[status]}`}
    >
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate font-medium" title={file.path}>
            {file.path}
          </h3>
          {status === 'done' && <ResultFacts result={result} />}
        </div>
        <div className="flex items-center gap-2">
          {status === 'done' && (
            <CopyButton text={result.text} label={`Copy text of ${file.name}`} />
          )}
          <StatusBadge status={status} />
        </div>
      </header>

      {status === 'done' && result.low_confidence && (
        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-100">
          Low OCR confidence: the scan may be blurry or in another language. Check this text before
          using it.
        </p>
      )}
      {status === 'done' && (
        <div className="animate-fade-in motion-reduce:animate-none">
          <ExtractedText text={result.text} />
        </div>
      )}
      {status === 'failed' && error && (
        <p className="text-sm text-red-700 dark:text-red-300">
          {error.message} <span className="font-mono text-xs opacity-70">({error.code})</span>
        </p>
      )}
      {status === 'cancelled' && (
        <p className="text-sm text-zinc-500">Skipped because the batch was cancelled.</p>
      )}
      {status === 'pending' && (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Waiting for a free slot; files are processed a few at a time.
        </p>
      )}
      {status === 'processing' && <ExtractingPlaceholder />}
    </article>
  )
}

function ResultFacts({ result }: { result: FileResult }) {
  const ocrPages = result.pages.filter((page) => page.method === 'ocr').length
  return (
    <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-600 dark:text-zinc-400">
      {result.method && <MethodBadge method={result.method} />}
      {result.method === 'mixed' && (
        <span>
          {plural(ocrPages, 'page')} of {result.pages.length} read with OCR
        </span>
      )}
      {result.mean_confidence !== null && (
        <span
          title="How sure the OCR engine is of the text it found. Text it did not find at all is not counted."
          className={`cursor-help underline decoration-dotted underline-offset-2 ${result.low_confidence ? 'font-medium text-amber-700 dark:text-amber-300' : ''}`}
        >
          OCR confidence {Math.round(result.mean_confidence)}%
        </span>
      )}
      <span>{plural(result.char_count, 'character')}</span>
      <span>{formatDuration(result.duration_ms)}</span>
    </p>
  )
}

/** Stands in for the text while the file is downloaded and read. */
function ExtractingPlaceholder() {
  return (
    <div className="space-y-3">
      <p className="inline-flex items-center gap-2 text-sm text-sky-800 dark:text-sky-200">
        <Spinner className="size-3.5" />
        Downloading and extracting text…
      </p>
      <div className="space-y-2 rounded-lg bg-zinc-50 p-3 dark:bg-zinc-950">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-11/12" />
        <Skeleton className="h-3 w-3/5" />
      </div>
    </div>
  )
}
