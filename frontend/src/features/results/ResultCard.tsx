import type { FileResult } from '../../api/types'
import { formatDuration, plural } from '../../lib/format'
import { StatusBadge } from '../batch/StatusBadge'
import { CopyButton } from './CopyButton'
import { ExtractedText } from './ExtractedText'
import { MethodBadge } from './MethodBadge'

export function ResultCard({ result }: { result: FileResult }) {
  const { file, status, error } = result
  return (
    <article
      aria-label={file.path}
      className="space-y-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800"
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
      {status === 'done' && <ExtractedText text={result.text} />}
      {status === 'failed' && error && (
        <p className="text-sm text-red-700 dark:text-red-300">
          {error.message} <span className="font-mono text-xs opacity-70">({error.code})</span>
        </p>
      )}
      {status === 'cancelled' && (
        <p className="text-sm text-zinc-500">Skipped because the batch was cancelled.</p>
      )}
      {(status === 'pending' || status === 'processing') && (
        <div
          className="h-16 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-800"
          aria-hidden="true"
        />
      )}
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
          className={result.low_confidence ? 'font-medium text-amber-700 dark:text-amber-300' : ''}
        >
          OCR confidence {Math.round(result.mean_confidence)}%
        </span>
      )}
      <span>{plural(result.char_count, 'character')}</span>
      <span>{formatDuration(result.duration_ms)}</span>
    </p>
  )
}
