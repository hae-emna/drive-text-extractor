import { useId, type ReactNode } from 'react'
import { plural } from '../lib/format'
import { pageLinks } from '../lib/pagination'
import type { Pager } from '../lib/usePagination'

interface PaginationProps {
  /** Accessible name of the navigation landmark, e.g. "File pages". */
  label: string
  /** What is being paged, singular: "file", "result". */
  noun: string
  pager: Pager<unknown>
  /** Called after the page changed, e.g. to bring the top of the list back into view. */
  onNavigate?: () => void
}

/** Page summary, page-size picker and page links. Hidden when everything fits on one page. */
export function Pagination({ label, noun, pager, onNavigate }: PaginationProps) {
  const sizeId = useId()
  const smallestSize = Math.min(...pager.pageSizes)
  if (pager.total <= smallestSize) return null

  function goTo(page: number) {
    pager.goTo(page)
    onNavigate?.()
  }

  return (
    <nav
      aria-label={label}
      className="flex flex-col gap-3 text-sm text-zinc-600 sm:flex-row sm:items-center sm:justify-between dark:text-zinc-400"
    >
      <p aria-live="polite">
        Showing{' '}
        <span className="font-medium text-zinc-900 tabular-nums dark:text-zinc-100">
          {pager.first}–{pager.last}
        </span>{' '}
        of {plural(pager.total, noun)}
      </p>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <span className="inline-flex items-center gap-2">
          <label htmlFor={sizeId}>Per page</label>
          <select
            id={sizeId}
            value={pager.pageSize}
            onChange={(event) => {
              pager.resize(Number(event.target.value))
              onNavigate?.()
            }}
            className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-zinc-900 focus-visible:outline-2 focus-visible:outline-lime-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
          >
            {pager.pageSizes.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </span>

        {pager.pageCount > 1 && (
          <ul className="flex items-center gap-1">
            <li>
              <PageButton
                label="Previous page"
                disabled={pager.page === 1}
                onClick={() => goTo(pager.page - 1)}
              >
                <Chevron direction="left" />
              </PageButton>
            </li>
            {pageLinks(pager.page, pager.pageCount).map((link, index) =>
              link === 'gap' ? (
                <li key={`gap-${index}`} aria-hidden="true" className="px-1 text-zinc-400">
                  …
                </li>
              ) : (
                <li key={link}>
                  <PageButton
                    label={`Page ${link}`}
                    current={link === pager.page}
                    onClick={() => goTo(link)}
                  >
                    {link}
                  </PageButton>
                </li>
              ),
            )}
            <li>
              <PageButton
                label="Next page"
                disabled={pager.page === pager.pageCount}
                onClick={() => goTo(pager.page + 1)}
              >
                <Chevron direction="right" />
              </PageButton>
            </li>
          </ul>
        )}
      </div>
    </nav>
  )
}

interface PageButtonProps {
  label: string
  current?: boolean
  disabled?: boolean
  onClick: () => void
  children: ReactNode
}

function PageButton({
  label,
  current = false,
  disabled = false,
  onClick,
  children,
}: PageButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-current={current ? 'page' : undefined}
      disabled={disabled}
      onClick={onClick}
      className={`inline-flex h-8 min-w-8 items-center justify-center rounded-md px-2 font-medium tabular-nums transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-lime-500 disabled:cursor-not-allowed disabled:opacity-40 ${
        current
          ? 'bg-zinc-900 text-white dark:bg-lime-300 dark:text-zinc-950'
          : 'text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800'
      }`}
    >
      {children}
    </button>
  )
}

function Chevron({ direction }: { direction: 'left' | 'right' }) {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" className="size-4">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d={
          direction === 'left'
            ? 'M12.79 5.23a.75.75 0 0 1-.02 1.06L8.83 10l3.94 3.71a.75.75 0 1 1-1.04 1.08l-4.5-4.25a.75.75 0 0 1 0-1.08l4.5-4.25a.75.75 0 0 1 1.06.02Z'
            : 'M7.21 14.77a.75.75 0 0 1 .02-1.06L11.17 10 7.23 6.29a.75.75 0 1 1 1.04-1.08l4.5 4.25a.75.75 0 0 1 0 1.08l-4.5 4.25a.75.75 0 0 1-1.06-.02Z'
        }
      />
    </svg>
  )
}
