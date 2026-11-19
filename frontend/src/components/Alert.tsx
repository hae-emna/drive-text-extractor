import type { ReactNode } from 'react'

type Tone = 'error' | 'warning' | 'info'

const TONES: Record<Tone, string> = {
  error:
    'border-red-300 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950 dark:text-red-100',
  warning:
    'border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100',
  info: 'border-zinc-300 bg-white text-zinc-800 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200',
}

interface AlertProps {
  tone: Tone
  title: string
  children?: ReactNode
}

export function Alert({ tone, title, children }: AlertProps) {
  return (
    // Errors interrupt screen readers; warnings and info are announced politely.
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={`rounded-lg border px-4 py-3 text-sm ${TONES[tone]}`}
    >
      <p className="font-medium">{title}</p>
      {children && <div className="mt-1 opacity-90">{children}</div>}
    </div>
  )
}
