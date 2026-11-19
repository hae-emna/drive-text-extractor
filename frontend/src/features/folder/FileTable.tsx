import { useEffect, useRef } from 'react'
import type { DriveFile, FileResult, SkippedFile } from '../../api/types'
import { Button } from '../../components/Button'
import { Pagination } from '../../components/Pagination'
import { fileTypeLabel, formatBytes, isFolderType, plural } from '../../lib/format'
import { revealTop } from '../../lib/dom'
import { usePagination } from '../../lib/usePagination'
import { StatusBadge } from '../batch/StatusBadge'
import { selectionState, toggle, toggleAll } from './selection'

const PAGE_SIZES = [25, 50, 100]

type Row = { kind: 'file'; file: DriveFile } | { kind: 'skipped'; item: SkippedFile; key: string }

interface FileTableProps {
  files: DriveFile[]
  /** Items that cannot be extracted: listed after the files, without a checkbox. */
  skipped?: SkippedFile[]
  selected: ReadonlySet<string>
  onSelectionChange: (selected: ReadonlySet<string>) => void
  disabled?: boolean
  /** Per-file batch results; adds a status column when present. */
  results?: ReadonlyMap<string, FileResult>
}

export function FileTable({
  files,
  skipped = [],
  selected,
  onSelectionChange,
  disabled = false,
  results,
}: FileTableProps) {
  const rows: Row[] = [
    ...files.map((file): Row => ({ kind: 'file', file })),
    ...skipped.map((item, index): Row => ({ kind: 'skipped', item, key: `skipped-${index}` })),
  ]
  const pager = usePagination(rows, PAGE_SIZES)
  const pageIds = pager.items.flatMap((row) => (row.kind === 'file' ? [row.file.id] : []))
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
      <SelectionToolbar
        files={files}
        skippedCount={skipped.length}
        selected={selected}
        disabled={disabled}
        onSelectionChange={onSelectionChange}
      />

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
                  disabled={disabled || pageIds.length === 0}
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
            {pager.items.map((row) =>
              row.kind === 'file' ? (
                <FileRow
                  key={row.file.id}
                  file={row.file}
                  checked={selected.has(row.file.id)}
                  onToggle={() => onSelectionChange(toggle(selected, row.file.id))}
                  disabled={disabled}
                  results={results}
                />
              ) : (
                <SkippedRow key={row.key} item={row.item} withStatus={results !== undefined} />
              ),
            )}
          </tbody>
        </table>
      </div>

      <Pagination
        label="File pages"
        noun={skipped.length > 0 ? 'item' : 'file'}
        pager={pager}
        onNavigate={() => revealTop(topRef.current)}
      />
    </div>
  )
}

interface SelectionToolbarProps {
  files: DriveFile[]
  skippedCount: number
  selected: ReadonlySet<string>
  disabled: boolean
  onSelectionChange: (selected: ReadonlySet<string>) => void
}

/** Selects or clears every extractable file, on every page, and counts what is listed. */
function SelectionToolbar({
  files,
  skippedCount,
  selected,
  disabled,
  onSelectionChange,
}: SelectionToolbarProps) {
  const allIds = files.map((file) => file.id)
  const selectedCount = allIds.filter((id) => selected.has(id)).length

  return (
    <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 text-sm">
      {allIds.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            className="px-3 py-1.5"
            disabled={disabled || allIds.length === 0 || selectedCount === allIds.length}
            onClick={() => onSelectionChange(new Set(allIds))}
          >
            Select all
          </Button>
          <Button
            variant="ghost"
            className="px-3 py-1.5"
            disabled={disabled || selectedCount === 0}
            onClick={() => onSelectionChange(new Set())}
          >
            Clear selection
          </Button>
          <p aria-live="polite" className="ml-1 text-zinc-600 tabular-nums dark:text-zinc-400">
            {selectedCount} of {plural(files.length, 'file')} selected
          </p>
        </div>
      )}
      {skippedCount > 0 && (
        <p className="text-zinc-500 tabular-nums">
          {plural(files.length + skippedCount, 'item')} listed · {skippedCount} cannot be extracted
        </p>
      )}
    </div>
  )
}

interface FileRowProps {
  file: DriveFile
  checked: boolean
  onToggle: () => void
  disabled: boolean
  results: ReadonlyMap<string, FileResult> | undefined
}

function FileRow({ file, checked, onToggle, disabled, results }: FileRowProps) {
  return (
    <tr
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
          checked={checked}
          onChange={onToggle}
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
      <td className="px-3 py-2 text-right tabular-nums">{formatBytes(file.size_bytes)}</td>
      {results && (
        <td className="px-3 py-2">
          <StatusCell result={results.get(file.id)} />
        </td>
      )}
    </tr>
  )
}

/** A listed item that cannot be extracted: no checkbox, a badge saying why at a glance. */
function SkippedRow({ item, withStatus }: { item: SkippedFile; withStatus: boolean }) {
  const folder = isFolderType(item.mime_type)
  return (
    <tr className="bg-zinc-50/60 text-zinc-500 dark:bg-zinc-950/40 dark:text-zinc-400">
      <td className="px-3 py-2">
        <BlockedIcon />
        <span className="sr-only">Cannot be selected</span>
      </td>
      <td className="max-w-0 px-3 py-2">
        <span className="flex items-center gap-2">
          <span className="truncate font-medium" title={item.name}>
            {item.name}
          </span>
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
              folder
                ? 'bg-zinc-200/70 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300'
                : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200'
            }`}
          >
            {folder ? 'subfolder' : 'unsupported'}
          </span>
        </span>
        <span className="block text-xs">{item.reason}</span>
      </td>
      <td className="px-3 py-2 font-mono text-xs">{fileTypeLabel(item.mime_type)}</td>
      <td className="px-3 py-2 text-right text-zinc-400">—</td>
      {withStatus && <td className="px-3 py-2 text-zinc-400">—</td>}
    </tr>
  )
}

function BlockedIcon() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      aria-hidden="true"
      className="size-4 text-zinc-400 dark:text-zinc-500"
    >
      <circle cx="10" cy="10" r="7" />
      <path d="m5.05 5.05 9.9 9.9" />
    </svg>
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
