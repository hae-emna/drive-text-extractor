import { useEffect, useRef, type ReactNode } from 'react'
import type { DriveFile, FileResult } from '../../api/types'
import { Pagination } from '../../components/Pagination'
import { fileTypeLabel, formatBytes, plural } from '../../lib/format'
import { revealTop } from '../../lib/dom'
import { usePagination } from '../../lib/usePagination'
import { StatusBadge } from '../batch/StatusBadge'
import { selectionState, toggle, toggleAll } from './selection'

const PAGE_SIZES = [25, 50, 100]

interface FileTableProps {
  files: DriveFile[]
  selected: ReadonlySet<string>
  onSelectionChange: (selected: ReadonlySet<string>) => void
  disabled?: boolean
  /** Per-file batch results; adds a status column when present. */
  results?: ReadonlyMap<string, FileResult>
}

export function FileTable({
  files,
  selected,
  onSelectionChange,
  disabled = false,
  results,
}: FileTableProps) {
  const pager = usePagination(files, PAGE_SIZES)
  const pageIds = pager.items.map((file) => file.id)
  const pageState = selectionState(selected, pageIds)
  const multiPage = pager.pageCount > 1
  const selectAllRef = useRef<HTMLInputElement>(null)
  const topRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // "indeterminate" has no HTML attribute; it can only be set from script.
    if (selectAllRef.current) selectAllRef.current.indeterminate = pageState === 'some'
  }, [pageState])

  return (
    <div ref={topRef} className="space-y-3">
      {multiPage && (
        <SelectionBanner
          files={files}
          pageSize={pageIds.length}
          selected={selected}
          pageFullySelected={pageState === 'all'}
          disabled={disabled}
          onSelectionChange={onSelectionChange}
        />
      )}

      <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-50 text-xs tracking-wide text-zinc-500 uppercase dark:bg-zinc-950 dark:text-zinc-400">
            <tr>
              <th scope="col" className="w-10 px-3 py-2">
                <input
                  ref={selectAllRef}
                  type="checkbox"
                  aria-label={multiPage ? 'Select all files on this page' : 'Select all files'}
                  checked={pageState === 'all'}
                  onChange={() => onSelectionChange(toggleAll(selected, pageIds))}
                  disabled={disabled}
                  className="size-4 accent-lime-600"
                />
              </th>
              <th scope="col" className="px-3 py-2 font-medium">
                Name
              </th>
              <th scope="col" className="px-3 py-2 font-medium">
                Type
              </th>
              <th scope="col" className="px-3 py-2 text-right font-medium">
                Size
              </th>
              {results && (
                <th scope="col" className="px-3 py-2 font-medium">
                  Status
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {pager.items.map((file) => (
              <tr
                key={file.id}
                className={
                  results?.get(file.id)?.status === 'processing'
                    ? 'bg-sky-50/70 transition-colors dark:bg-sky-950/30'
                    : 'transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/50'
                }
              >
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    aria-label={`Select ${file.path}`}
                    checked={selected.has(file.id)}
                    onChange={() => onSelectionChange(toggle(selected, file.id))}
                    disabled={disabled}
                    className="size-4 accent-lime-600"
                  />
                </td>
                <td className="max-w-0 px-3 py-2">
                  <span className="block truncate font-medium" title={file.path}>
                    {file.name}
                  </span>
                  {file.path !== file.name && (
                    <span className="block truncate text-xs text-zinc-500">{file.path}</span>
                  )}
                </td>
                <td className="px-3 py-2 font-mono text-xs">{fileTypeLabel(file.mime_type)}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {formatBytes(file.size_bytes)}
                </td>
                {results && (
                  <td className="px-3 py-2">
                    <StatusCell result={results.get(file.id)} />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination
        label="File pages"
        noun="file"
        pager={pager}
        onNavigate={() => revealTop(topRef.current)}
      />
    </div>
  )
}

interface SelectionBannerProps {
  files: DriveFile[]
  pageSize: number
  selected: ReadonlySet<string>
  pageFullySelected: boolean
  disabled: boolean
  onSelectionChange: (selected: ReadonlySet<string>) => void
}

/** Extends a page selection to every page, or clears a selection that spans every page. */
function SelectionBanner({
  files,
  pageSize,
  selected,
  pageFullySelected,
  disabled,
  onSelectionChange,
}: SelectionBannerProps) {
  const allIds = files.map((file) => file.id)
  const everything = selectionState(selected, allIds) === 'all'
  if (!everything && !pageFullySelected) return null

  return (
    <p
      aria-live="polite"
      className="flex flex-wrap items-center justify-center gap-x-2 rounded-lg bg-lime-50 px-4 py-2 text-sm text-lime-950 dark:bg-lime-950/40 dark:text-lime-100"
    >
      {everything ? (
        <>
          All {plural(files.length, 'file')} are selected.
          <BannerButton disabled={disabled} onClick={() => onSelectionChange(new Set())}>
            Clear selection
          </BannerButton>
        </>
      ) : (
        <>
          All {plural(pageSize, 'file')} on this page are selected.
          <BannerButton disabled={disabled} onClick={() => onSelectionChange(new Set(allIds))}>
            Select all {plural(files.length, 'file')}
          </BannerButton>
        </>
      )}
    </p>
  )
}

function BannerButton(props: { disabled: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      {...props}
      className="font-semibold underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-lime-500 disabled:cursor-not-allowed disabled:opacity-50"
    />
  )
}

function StatusCell({ result }: { result: FileResult | undefined }) {
  if (!result) return <span className="text-zinc-400">—</span>
  return (
    <span className="inline-flex items-center gap-2">
      <StatusBadge status={result.status} />
      {result.error && <span className="sr-only">{result.error.message}</span>}
    </span>
  )
}
