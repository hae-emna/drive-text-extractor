import { useState } from 'react'
import { Alert } from './components/Alert'
import { Section } from './components/Section'
import { FileTable } from './features/folder/FileTable'
import { LinkForm } from './features/folder/LinkForm'
import { SkippedFiles } from './features/folder/SkippedFiles'
import { selectedInOrder, toggle, toggleAll } from './features/folder/selection'
import { useFolderListing } from './features/folder/useFolderListing'
import { plural } from './lib/format'

export default function App() {
  const { state: listing, load } = useFolderListing()
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set())

  const files = listing.status === 'loaded' ? listing.listing.files : []
  const fileIds = files.map((file) => file.id)
  const selectedIds = selectedInOrder(selected, fileIds)

  function handleList(link: string, recursive: boolean) {
    setSelected(new Set())
    void load(link, recursive)
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto max-w-5xl px-4 py-5">
          <h1 className="text-xl font-semibold tracking-tight">Drive Text Extractor</h1>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
            Extract the text of the PDFs and images in a public Google Drive folder. Native PDFs go
            through a PDF parser, images and scanned pages through OCR.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        <Section step="01" title="Paste a folder link">
          <LinkForm busy={listing.status === 'loading'} onSubmit={handleList} />
        </Section>

        {listing.status === 'error' && (
          <Alert tone="error" title="This folder could not be listed">
            {listing.error.message}
          </Alert>
        )}

        {listing.status === 'loaded' && (
          <Section
            step="02"
            title={`Choose files in “${listing.listing.folder.name}”`}
            aside={
              <p className="text-sm text-zinc-600 dark:text-zinc-400" aria-live="polite">
                {selectedIds.length} of {plural(files.length, 'file')} selected
              </p>
            }
          >
            <div className="space-y-4">
              {listing.listing.truncated && (
                <Alert tone="warning" title="Large folder">
                  Only the first {plural(files.length, 'file')} are listed.
                </Alert>
              )}
              {files.length === 0 ? (
                <Alert tone="info" title="Nothing to extract here">
                  This folder has no PDF, PNG or JPEG files
                  {listing.request.recursive ? '.' : ' at its top level. Try including subfolders.'}
                </Alert>
              ) : (
                <FileTable
                  files={files}
                  selected={selected}
                  onToggle={(id) => setSelected((current) => toggle(current, id))}
                  onToggleAll={() => setSelected((current) => toggleAll(current, fileIds))}
                />
              )}
              <SkippedFiles skipped={listing.listing.skipped} />
            </div>
          </Section>
        )}
      </main>
    </div>
  )
}
