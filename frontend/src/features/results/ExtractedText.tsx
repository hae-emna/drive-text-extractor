import { useId, useState } from 'react'

const COLLAPSED_CHARS = 1200

/**
 * Extracted text, with its line breaks kept.
 *
 * `unicode-bidi: plaintext` gives every line its own direction from its first strong character,
 * so an Arabic line renders right-to-left even between French or English lines.
 */
export function ExtractedText({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false)
  const id = useId()
  const long = text.length > COLLAPSED_CHARS

  if (!text) {
    return <p className="text-sm text-zinc-500 italic">No text was found in this file.</p>
  }

  return (
    <div>
      <pre
        id={id}
        dir="auto"
        className={`overflow-hidden rounded-lg bg-zinc-50 p-3 font-sans text-sm leading-relaxed whitespace-pre-wrap [unicode-bidi:plaintext] dark:bg-zinc-950 ${long && !expanded ? 'max-h-64' : ''}`}
      >
        {text}
      </pre>
      {long && (
        <button
          type="button"
          aria-controls={id}
          aria-expanded={expanded}
          onClick={() => setExpanded((value) => !value)}
          className="mt-2 text-sm font-medium text-lime-700 hover:underline dark:text-lime-300"
        >
          {expanded ? 'Show less' : `Show all ${text.length.toLocaleString('en')} characters`}
        </button>
      )}
    </div>
  )
}
