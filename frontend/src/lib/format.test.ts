import { describe, expect, it } from 'vitest'
import { fileTypeLabel, formatBytes, formatDuration, plural } from './format'

describe('formatBytes', () => {
  it.each([
    [null, '—'],
    [0, '0 B'],
    [999, '999 B'],
    [1500, '1.5 KB'],
    [48_211, '48 KB'],
    [2_400_000, '2.4 MB'],
    [3_000_000_000, '3.0 GB'],
  ])('formats %s as %s', (bytes, expected) => {
    expect(formatBytes(bytes)).toBe(expected)
  })
})

describe('formatDuration', () => {
  it.each([
    [null, '—'],
    [312, '312 ms'],
    [2400, '2.4 s'],
  ])('formats %s as %s', (ms, expected) => {
    expect(formatDuration(ms)).toBe(expected)
  })
})

describe('fileTypeLabel', () => {
  it('uses short labels for supported types and falls back to the subtype', () => {
    expect(fileTypeLabel('application/pdf')).toBe('PDF')
    expect(fileTypeLabel('image/jpeg')).toBe('JPEG')
    expect(fileTypeLabel('image/webp')).toBe('WEBP')
  })
})

describe('plural', () => {
  it('picks the right form', () => {
    expect(plural(1, 'file')).toBe('1 file')
    expect(plural(3, 'file')).toBe('3 files')
  })
})
