import type { DriveFile, FileResult, FolderListing, Health, Job } from '../api/types'

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
  kind: 'folder',
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

export const HEALTH: Health = {
  status: 'ok',
  version: '0.1.0',
  source: 'google_drive',
  languages: [
    { code: 'eng', name: 'English', installed: true },
    { code: 'fra', name: 'French', installed: true },
    { code: 'ara', name: 'Arabic', installed: true },
  ],
}

export function result(
  file: DriveFile,
  overrides: Partial<FileResult> & Pick<FileResult, 'status'>,
): FileResult {
  return {
    file,
    method: null,
    mean_confidence: null,
    low_confidence: false,
    char_count: 0,
    duration_ms: null,
    text: '',
    pages: [],
    error: null,
    ...overrides,
  }
}

export function job(files: FileResult[], overrides: Partial<Job> = {}): Job {
  const count = (status: FileResult['status']) => files.filter((f) => f.status === status).length
  const finished = files.every((f) => ['done', 'failed', 'cancelled'].includes(f.status))
  return {
    id: 'job-1',
    status: finished ? 'finished' : 'running',
    created_at: '2026-11-19T09:00:00Z',
    finished_at: finished ? '2026-11-19T09:00:05Z' : null,
    cancel_requested: false,
    folder: LISTING.folder,
    languages: ['eng', 'fra'],
    summary: {
      total: files.length,
      pending: count('pending'),
      processing: count('processing'),
      done: count('done'),
      failed: count('failed'),
      cancelled: count('cancelled'),
    },
    files,
    ...overrides,
  }
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
