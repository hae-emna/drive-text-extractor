import { useEffect, useState } from 'react'
import { Button } from '../../components/Button'

/** How long the button says "Copied" before going back to its label. */
const COPIED_FEEDBACK_MS = 2000

export function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) return
    const timer = setTimeout(() => setCopied(false), COPIED_FEEDBACK_MS)
    return () => clearTimeout(timer)
  }, [copied])

  // The Clipboard API only exists in secure contexts (HTTPS or localhost).
  if (!text || !navigator.clipboard) return null

  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
    } catch {
      // Permission denied: nothing useful to do, the text stays selectable.
    }
  }

  return (
    <Button
      variant="ghost"
      className="px-2 py-1 text-xs"
      onClick={() => void copy()}
      aria-label={label}
    >
      <span aria-live="polite">{copied ? 'Copied' : 'Copy'}</span>
    </Button>
  )
}
