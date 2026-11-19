import { useId, useState, type FormEvent } from 'react'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'

interface LinkFormProps {
  busy: boolean
  onSubmit: (link: string, recursive: boolean) => void
}

export function LinkForm({ busy, onSubmit }: LinkFormProps) {
  const [link, setLink] = useState('')
  const [recursive, setRecursive] = useState(false)
  const inputId = useId()
  const hintId = useId()
  const trimmed = link.trim()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (trimmed && !busy) onSubmit(trimmed, recursive)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <label htmlFor={inputId} className="block text-sm font-medium">
        Public Google Drive folder link
      </label>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          id={inputId}
          type="text"
          inputMode="url"
          autoComplete="off"
          spellCheck={false}
          placeholder="https://drive.google.com/drive/folders/…"
          aria-describedby={hintId}
          value={link}
          onChange={(event) => setLink(event.target.value)}
          className="min-w-0 flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-lime-500 focus:outline-2 focus:outline-lime-500/40 dark:border-zinc-700 dark:bg-zinc-950"
        />
        <Button type="submit" disabled={!trimmed || busy}>
          {busy && <Spinner />}
          {busy ? 'Listing…' : 'List files'}
        </Button>
      </div>
      <div className="flex flex-col gap-2 text-sm text-zinc-600 sm:flex-row sm:items-center sm:justify-between dark:text-zinc-400">
        <p id={hintId}>
          Share the folder as “Anyone with the link”. PDF, PNG and JPEG files are processed.
        </p>
        <label className="inline-flex shrink-0 items-center gap-2">
          <input
            type="checkbox"
            checked={recursive}
            onChange={(event) => setRecursive(event.target.checked)}
            className="size-4 accent-lime-600"
          />
          Include subfolders
        </label>
      </div>
    </form>
  )
}
