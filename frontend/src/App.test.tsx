import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { fakeBackend, LISTING } from './test/fixtures'

const LINK = 'https://drive.google.com/drive/folders/folder-1'

afterEach(() => {
  vi.unstubAllGlobals()
})

async function listFolder() {
  const user = userEvent.setup()
  render(<App />)
  await user.type(screen.getByLabelText('Public Google Drive folder link'), LINK)
  await user.click(screen.getByRole('button', { name: 'List files' }))
  return user
}

describe('App', () => {
  it('lists the folder, keeps the selection count visible and explains skipped files', async () => {
    vi.stubGlobal('fetch', vi.fn(fakeBackend({ 'POST /api/folders/list': { body: LISTING } })))
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
          'POST /api/folders/list': {
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
    vi.stubGlobal('fetch', vi.fn(fakeBackend({ 'POST /api/folders/list': { body: empty } })))
    await listFolder()

    expect(await screen.findByText(/Try including subfolders/)).toBeInTheDocument()
  })
})
