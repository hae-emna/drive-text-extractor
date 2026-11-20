import { useState } from 'react'
import type { FileResult, LanguageCode } from './api/types'
import { Alert } from './components/Alert'
import { Button } from './components/Button'
import { Section } from './components/Section'
import { Spinner } from './components/Spinner'
import { BatchProgress } from './features/batch/BatchProgress'
import { DEFAULT_LANGUAGES, usableLanguages } from './features/batch/languages'
import { LanguagePicker } from './features/batch/LanguagePicker'
import { POLL_INTERVAL_MS, useBatchJob } from './features/batch/useBatchJob'
import { useHealth } from './features/batch/useHealth'
import { FileTable } from './features/folder/FileTable'
import { LinkForm } from './features/folder/LinkForm'
import { ListingSkeleton } from './features/folder/ListingSkeleton'
import { selectedInOrder } from './features/folder/selection'
import { useFolderListing } from './features/folder/useFolderListing'
import { ResultList } from './features/results/ResultList'
import { plural } from './lib/format'

interface AppProps {
  pollIntervalMs?: number
}

export default function App({ pollIntervalMs = POLL_INTERVAL_MS }: AppProps) {
  const health = useHealth()
  const { state: listing, load } = useFolderListing()
  const batch = useBatchJob(pollIntervalMs)
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set())
  const [chosenLanguages, setLanguages] = useState<LanguageCode[]>(['eng', 'fra'])
  const offeredLanguages = health?.languages ?? DEFAULT_LANGUAGES
  const languages = usableLanguages(chosenLanguages, offeredLanguages)

  const files = listing.status === 'loaded' ? listing.listing.files : []
  const fileIds = files.map((file) => file.id)
  const selectedIds = selectedInOrder(selected, fileIds)
  const job = batch.job
  const busy = batch.starting || job?.status === 'running'
  const results = job
    ? new Map<string, FileResult>(job.files.map((result) => [result.file.id, result]))
    : undefined

  async function handleList(link: string, recursive: boolean) {
    setSelected(new Set())
    batch.reset()
    const result = await load(link, recursive)
    // A link to one file means that file is what the user wants: select it for them.
    if (result?.kind === 'file') setSelected(new Set(result.files.map((file) => file.id)))
  }

  function handleExtract() {
    if (listing.status !== 'loaded' || selectedIds.length === 0) return
    void batch.start({
      link: listing.request.link,
      recursive: listing.request.recursive,
      file_ids: selectedIds,
      languages,
    })
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto max-w-5xl px-4 py-5">
          <h1 className="text-xl font-semibold tracking-tight">Drive Text Extractor</h1>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
            Extract the text of the PDFs and images shared on Google Drive, from a whole folder or a
            single file. Native PDFs go through a PDF parser, images and scanned pages through OCR.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        <Section step="01" title="Paste a Drive link">
          <fieldset disabled={busy}>
            <LinkForm
              busy={listing.status === 'loading'}
              demoMode={health?.source === 'local'}
              onSubmit={(link, recursive) => void handleList(link, recursive)}
            />
          </fieldset>
        </Section>

        {listing.status === 'loading' && (
          <Section step="02" title="Listing files…" busy>
            <ListingSkeleton recursive={listing.request.recursive} />
          </Section>
        )}

        {listing.status === 'error' && (
          <Alert tone="error" title="This folder could not be listed">
            {listing.error.message}
          </Alert>
        )}

        {listing.status === 'loaded' && (
          <>
            <Section
              step="02"
              title={
                listing.listing.kind === 'file'
                  ? `File “${listing.listing.folder.name}”`
                  : `Choose files in “${listing.listing.folder.name}”`
              }
            >
              <div className="space-y-4">
                {listing.listing.truncated && (
                  <Alert tone="warning" title="Large folder">
                    Only the first {plural(files.length, 'file')} are listed.
                  </Alert>
                )}
                {files.length === 0 && listing.listing.kind === 'file' ? (
                  <Alert tone="info" title="This file cannot be extracted">
                    {listing.listing.skipped[0]?.reason ??
                      'Only PDF, PNG and JPEG files are processed.'}
                  </Alert>
                ) : (
                  <>
                    {files.length === 0 && (
                      <Alert tone="info" title="Nothing to extract here">
                        This folder has no PDF, PNG or JPEG files
                        {listing.request.recursive
                          ? '.'
                          : ' at its top level. Try including subfolders.'}
                      </Alert>
                    )}
                    {files.length + listing.listing.skipped.length > 0 && (
                      <FileTable
                        files={files}
                        skipped={listing.listing.skipped}
                        selected={selected}
                        onSelectionChange={setSelected}
                        disabled={busy}
                        results={results}
                      />
                    )}
                  </>
                )}
              </div>
            </Section>

            {files.length > 0 && (
              <Section step="03" title="Extract text">
                <div className="space-y-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <LanguagePicker
                      languages={offeredLanguages}
                      value={languages}
                      onChange={setLanguages}
                      disabled={busy}
                    />
                    <Button onClick={handleExtract} disabled={selectedIds.length === 0 || busy}>
                      {batch.starting && <Spinner />}
                      {batch.starting
                        ? 'Starting…'
                        : selectedIds.length === 0
                          ? 'Select files to extract'
                          : `Extract text from ${plural(selectedIds.length, 'file')}`}
                    </Button>
                  </div>
                  <p className="text-xs text-zinc-500">
                    Languages are used for images and scanned PDF pages. Pages with a text layer are
                    read directly.
                  </p>
                  {batch.error && (
                    <Alert tone="error" title="The batch could not be processed">
                      {batch.error.message}
                    </Alert>
                  )}
                  {batch.connectionLost && (
                    <Alert tone="warning" title="Connection lost">
                      Retrying… processing continues on the server.
                    </Alert>
                  )}
                  {job && (
                    <BatchProgress key={job.id} job={job} onCancel={() => void batch.cancel()} />
                  )}
                </div>
              </Section>
            )}

            {job && (
              <Section step="04" title="Read the results">
                <ResultList job={job} onSelectFailed={(ids) => setSelected(new Set(ids))} />
              </Section>
            )}
          </>
        )}
      </main>

      <footer className="mx-auto max-w-5xl px-4 pb-10 text-xs text-zinc-500">
        Open source under the MIT licence ·{' '}
        <a href="/third-party-licenses.md" className="underline hover:text-zinc-800">
          Third-party licences
        </a>
      </footer>
    </div>
  )
}
