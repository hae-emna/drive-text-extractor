import type { DriveFile, FolderListing } from '../api/types'

export function driveFile(
  overrides: Partial<DriveFile> & Pick<DriveFile, 'id' | 'name'>,
): DriveFile {
  return {
    path: overrides.name,
    mime_type: 'application/pdf',
    size_bytes: 48_211,
    modified_time: '2026-11-01T10:00:00Z',
    ...overrides,
  }
}

export const LISTING: FolderListing = {
  folder: { id: 'folder-1', name: 'Invoices 2026' },
  files: [
    driveFile({ id: 'pdf-1', name: 'invoice.pdf' }),
    driveFile({ id: 'png-1', name: 'receipt.png', mime_type: 'image/png', size_bytes: 2_400_000 }),
    driveFile({ id: 'jpg-1', name: 'scan.jpg', path: 'archive/scan.jpg', mime_type: 'image/jpeg' }),
  ],
  skipped: [
    {
      name: 'notes',
      mime_type: 'application/vnd.google-apps.document',
      reason: 'Google Docs, Sheets and Slides files are not supported. Export them to PDF first.',
    },
  ],
  truncated: false,
}

/** Replace fetch with a router of canned JSON responses keyed by "METHOD /path". */
export function fakeBackend(routes: Record<string, { status?: number; body: unknown }>) {
  return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const key = `${init?.method ?? 'GET'} ${String(input)}`
    const route = routes[key]
    if (!route) throw new Error(`Unexpected request: ${key}`)
    return new Response(JSON.stringify(route.body), { status: route.status ?? 200 })
  }
}
