import { useEffect, useRef } from 'react'
import type { DriveFile, FileResult } from '../../api/types'
import { fileTypeLabel, formatBytes } from '../../lib/format'
import { StatusBadge } from '../batch/StatusBadge'
import { selectionState } from './selection'

interface FileTableProps {
  files: DriveFile[]
  selected: ReadonlySet<string>
  onToggle: (id: string) => void
  onToggleAll: () => void
  disabled?: boolean
  /** Per-file batch results; adds a status column when present. */
  results?: ReadonlyMap<string, FileResult>
}

export function FileTable({
  files,
  selected,
  onToggle,
  onToggleAll,
  disabled = false,
  results,
}: FileTableProps) {
  const state = selectionState(
    selected,
    files.map((file) => file.id),
  )
  const selectAllRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    // "indeterminate" has no HTML attribute; it can only be set from script.
    if (selectAllRef.current) selectAllRef.current.indeterminate = state === 'some'
  }, [state])

  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
          <tr>
            <th scope="col" className="w-10 px-3 py-2">
              <input
                ref={selectAllRef}
                type="checkbox"
                aria-label="Select all files"
                checked={state === 'all'}
                onChange={onToggleAll}
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
          {files.map((file) => (
            <tr key={file.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
              <td className="px-3 py-2">
                <input
                  type="checkbox"
                  aria-label={`Select ${file.path}`}
                  checked={selected.has(file.id)}
                  onChange={() => onToggle(file.id)}
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
          ))}
        </tbody>
      </table>
    </div>
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
