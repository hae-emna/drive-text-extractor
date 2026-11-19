import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { fakeBackend, HEALTH, job, LISTING, result } from './test/fixtures'

const LINK = 'https://drive.google.com/drive/folders/folder-1'

afterEach(() => {
  vi.unstubAllGlobals()
})

async function listFolder() {
  const user = userEvent.setup()
  render(<App pollIntervalMs={5} />)
  await user.type(screen.getByLabelText('Public Google Drive link (folder or file)'), LINK)
  await user.click(screen.getByRole('button', { name: 'List files' }))
  return user
}

describe('App', () => {
  it('lists the folder, keeps the selection count visible and explains skipped files', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        fakeBackend({
          'GET /api/health': { body: HEALTH },
          'POST /api/files/list': { body: LISTING },
        }),
      ),
    )
    const user = await listFolder()

    expect(await screen.findByText(/Choose files in “Invoices 2026”/)).toBeInTheDocument()
    expect(screen.getByText('0 of 3 files selected')).toBeInTheDocument()

    await user.click(screen.getByRole('checkbox', { name: 'Select all files' }))
    expect(screen.getByText('3 of 3 files selected')).toBeInTheDocument()

    await user.click(screen.getByText('1 item not offered for extraction'))
    expect(screen.getByText(/Export them to PDF first/)).toBeVisible()
  })

  it('shows the backend message when the folder cannot be listed', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        fakeBackend({
          'POST /api/files/list': {
            status: 404,
            body: {
              error: { code: 'folder_not_found', message: 'Folder not found or not public.' },
            },
          },
        }),
      ),
    )
    await listFolder()

    expect(await screen.findByRole('alert')).toHaveTextContent('Folder not found or not public.')
  })

  it('suggests including subfolders when the top level has nothing to extract', async () => {
    const empty = { ...LISTING, files: [] }
    vi.stubGlobal('fetch', vi.fn(fakeBackend({ 'POST /api/files/list': { body: empty } })))
    await listFolder()

    expect(await screen.findByText(/Try including subfolders/)).toBeInTheDocument()
  })
})

describe('App batch', () => {
  const [pdf, png] = LISTING.files as [(typeof LISTING.files)[0], (typeof LISTING.files)[0]]
  const running = job([result(pdf, { status: 'processing' }), result(png, { status: 'pending' })])
  const finished = job([
    result(pdf, { status: 'done', method: 'pdf_parser', text: 'Invoice text', char_count: 12 }),
    result(png, {
      status: 'failed',
      error: { code: 'corrupt_file', message: 'This file is damaged.' },
    }),
  ])

  it('runs the selected files and follows each status until the batch finishes', async () => {
    const fetchMock = vi.fn(
      fakeBackend({
        'GET /api/health': { body: HEALTH },
        'POST /api/files/list': { body: LISTING },
        'POST /api/jobs': { status: 202, body: running },
        'GET /api/jobs/job-1': { body: finished },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const user = await listFolder()
    await user.click(await screen.findByRole('checkbox', { name: 'Select invoice.pdf' }))
    await user.click(screen.getByRole('checkbox', { name: 'Select receipt.png' }))
    await user.click(screen.getByLabelText('Arabic'))

    await user.click(screen.getByRole('button', { name: 'Extract text from 2 files' }))

    expect(await screen.findByText(/Finished: 2 files/)).toBeInTheDocument()
    expect(screen.getByText('1 failed', { exact: false })).toBeInTheDocument()
    const table = within(screen.getByRole('table'))
    expect(table.getByText('done')).toBeInTheDocument()
    expect(table.getByText('failed')).toBeInTheDocument()
    const results = within(screen.getByRole('region', { name: /Read the results/ }))
    expect(results.getByText('Invoice text')).toBeInTheDocument()
    expect(results.getByText(/This file is damaged/)).toBeInTheDocument()
    expect(results.getByRole('link', { name: 'Export JSON' })).toBeInTheDocument()
    const startCall = fetchMock.mock.calls.find(([url]) => url === '/api/jobs')
    expect(JSON.parse(startCall?.[1]?.body as string)).toEqual({
      link: LINK,
      recursive: false,
      file_ids: ['pdf-1', 'png-1'],
      languages: ['eng', 'fra', 'ara'],
    })
  })

  it('shows why a batch could not start', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        fakeBackend({
          'GET /api/health': { body: HEALTH },
          'POST /api/files/list': { body: LISTING },
          'POST /api/jobs': {
            status: 400,
            body: {
              error: {
                code: 'invalid_selection',
                message: '1 selected file(s) are no longer in this folder. Reload the list.',
              },
            },
          },
        }),
      ),
    )
    const user = await listFolder()
    await user.click(await screen.findByRole('checkbox', { name: 'Select all files' }))

    await user.click(screen.getByRole('button', { name: 'Extract text from 3 files' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('no longer in this folder')
  })
})

describe('App demo mode', () => {
  it('explains the local: link syntax when the server reads local folders', async () => {
    const health = { ...HEALTH, source: 'local' as const }
    vi.stubGlobal('fetch', vi.fn(fakeBackend({ 'GET /api/health': { body: health } })))
    render(<App />)

    expect(await screen.findByText(/Demo mode: the server reads its sample folder/)).toBeVisible()
    expect(screen.getByLabelText('Public Google Drive link (folder or file)')).toHaveAttribute(
      'placeholder',
      'local:',
    )
  })
})

describe('App single-file links', () => {
  it('lists a linked file under its own name and selects it', async () => {
    const single = {
      kind: 'file' as const,
      folder: { id: 'pdf-1', name: 'invoice.pdf' },
      files: [LISTING.files[0]!],
      skipped: [],
      truncated: false,
    }
    vi.stubGlobal(
      'fetch',
      vi.fn(
        fakeBackend({
          'GET /api/health': { body: HEALTH },
          'POST /api/files/list': { body: single },
        }),
      ),
    )
    await listFolder()

    expect(await screen.findByText('File “invoice.pdf”')).toBeInTheDocument()
    expect(screen.getByText('1 of 1 file selected')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Extract text from 1 file' })).toBeEnabled()
  })

  it('explains why a linked file cannot be extracted', async () => {
    const doc = {
      kind: 'file' as const,
      folder: { id: 'doc-1', name: 'notes' },
      files: [],
      skipped: [LISTING.skipped[0]!],
      truncated: false,
    }
    vi.stubGlobal(
      'fetch',
      vi.fn(
        fakeBackend({ 'GET /api/health': { body: HEALTH }, 'POST /api/files/list': { body: doc } }),
      ),
    )
    await listFolder()

    expect(await screen.findByText('This file cannot be extracted')).toBeInTheDocument()
    expect(screen.getByText(/Export them to PDF first/)).toBeInTheDocument()
  })
})
