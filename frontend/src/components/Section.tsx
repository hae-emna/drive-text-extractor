import type { ReactNode } from 'react'

interface SectionProps {
  step: string
  title: string
  aside?: ReactNode
  children: ReactNode
}

/** One numbered step of the flow: link, files, results. */
export function Section({ step, title, aside, children }: SectionProps) {
  const headingId = `step-${step}`
  return (
    <section
      aria-labelledby={headingId}
      className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h2 id={headingId} className="flex items-baseline gap-3 text-base font-semibold">
          <span className="font-mono text-xs text-lime-700 dark:text-lime-300">{step}</span>
          {title}
        </h2>
        {aside}
      </div>
      {children}
    </section>
  )
}
