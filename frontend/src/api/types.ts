// Mirrors backend/src/drive_text_extractor/api/schemas.py. Keep both in sync.

export type ExtractionMethod = 'pdf_parser' | 'ocr' | 'mixed'
export type FileStatus = 'pending' | 'processing' | 'done' | 'failed' | 'cancelled'
export type LanguageCode = 'eng' | 'fra' | 'ara'

export interface ErrorBody {
  code: string
  message: string
}

export interface DriveFile {
  id: string
  name: string
  path: string
  mime_type: string
  size_bytes: number | null
  modified_time: string | null
}

export interface SkippedFile {
  name: string
  mime_type: string
  reason: string
}

export interface Folder {
  id: string
  name: string
}

export interface FolderListing {
  kind: 'folder' | 'file'
  /** The folder, or the file itself when the link points to a single file. */
  folder: Folder
  files: DriveFile[]
  skipped: SkippedFile[]
  truncated: boolean
}

export interface Page {
  number: number
  method: ExtractionMethod
  confidence: number | null
  text: string
}

export interface FileResult {
  file: DriveFile
  status: FileStatus
  method: ExtractionMethod | null
  mean_confidence: number | null
  low_confidence: boolean
  char_count: number
  duration_ms: number | null
  text: string
  pages: Page[]
  error: ErrorBody | null
}

export interface Summary {
  total: number
  pending: number
  processing: number
  done: number
  failed: number
  cancelled: number
}

export interface Job {
  id: string
  status: 'running' | 'finished'
  created_at: string
  finished_at: string | null
  cancel_requested: boolean
  folder: Folder
  languages: LanguageCode[]
  summary: Summary
  files: FileResult[]
}

export interface Language {
  code: LanguageCode
  name: string
  installed: boolean
}

export interface Health {
  status: 'ok'
  version: string
  source: 'google_drive' | 'local'
  languages: Language[]
}

export interface StartJobRequest {
  link: string
  file_ids: string[]
  languages: LanguageCode[]
  recursive: boolean
}
