import type { FolderListing, Health, Job, StartJobRequest } from './types'

/** Every failure the UI can show: backend error envelopes, HTTP errors and network errors. */
export class ApiError extends Error {
  readonly code: string
  readonly status: number

  constructor(code: string, message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ApiError(
      'network_error',
      'Cannot reach the server. Check that the backend is running.',
      0,
    )
  }
  if (!response.ok) {
    throw await errorFrom(response)
  }
  return (await response.json()) as T
}

async function errorFrom(response: Response): Promise<ApiError> {
  const body: unknown = await response.json().catch(() => null)
  const error = (body as { error?: { code?: unknown; message?: unknown } } | null)?.error
  if (typeof error?.code === 'string' && typeof error.message === 'string') {
    return new ApiError(error.code, error.message, response.status)
  }
  return new ApiError(
    'http_error',
    `The server answered with HTTP ${response.status}.`,
    response.status,
  )
}

const post = (body?: unknown): RequestInit => ({
  method: 'POST',
  body: body === undefined ? undefined : JSON.stringify(body),
})

export const api = {
  health: () => request<Health>('/api/health'),

  listFolder: (link: string, recursive: boolean) =>
    request<FolderListing>('/api/folders/list', post({ link, recursive })),

  startJob: (body: StartJobRequest) => request<Job>('/api/jobs', post(body)),

  getJob: (jobId: string) => request<Job>(`/api/jobs/${encodeURIComponent(jobId)}`),

  cancelJob: (jobId: string) =>
    request<Job>(`/api/jobs/${encodeURIComponent(jobId)}/cancel`, post()),

  exportUrl: (jobId: string) => `/api/jobs/${encodeURIComponent(jobId)}/export`,
}
