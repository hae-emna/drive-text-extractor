/** A shimmering placeholder for content that is still loading. Size it with `className`. */
export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`skeleton animate-shimmer rounded motion-reduce:animate-none ${className}`}
    />
  )
}

/** A thin bar for work whose length is unknown. */
export function IndeterminateBar({ label }: { label: string }) {
  return (
    <div
      role="progressbar"
      aria-label={label}
      className="h-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800"
    >
      <div className="animate-indeterminate h-full w-2/5 rounded-full bg-lime-500 motion-reduce:w-full motion-reduce:animate-none motion-reduce:opacity-60" />
    </div>
  )
}
