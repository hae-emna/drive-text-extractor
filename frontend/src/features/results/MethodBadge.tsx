import type { ExtractionMethod } from '../../api/types'

const LABELS: Record<ExtractionMethod, string> = {
  pdf_parser: 'PDF parser',
  ocr: 'OCR',
  mixed: 'PDF parser + OCR',
}

export function MethodBadge({ method }: { method: ExtractionMethod }) {
  return (
    <span className="rounded-md border border-zinc-300 px-1.5 py-0.5 font-mono text-xs dark:border-zinc-700">
      {LABELS[method]}
    </span>
  )
}
