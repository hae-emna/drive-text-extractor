import { describe, expect, it } from 'vitest'
import {
  estimateRemainingMs,
  fileTypeLabel,
  formatBytes,
  formatDuration,
  formatElapsed,
  formatRemaining,
  plural,
} from './format'

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

describe('formatElapsed', () => {
  it.each([
    [0, '0 s'],
    [8_400, '8 s'],
    [60_000, '1 min 00 s'],
    [125_000, '2 min 05 s'],
  ])('formats %i ms as %s', (ms, expected) => {
    expect(formatElapsed(ms)).toBe(expected)
  })
})

describe('estimateRemainingMs', () => {
  it('extrapolates the pace so far', () => {
    expect(estimateRemainingMs(10_000, 2, 6)).toBe(20_000)
  })

  it.each([
    [10_000, 0, 6],
    [10_000, 6, 6],
    [500, 1, 6],
  ])('has no estimate yet or any more (%i ms, %i of %i)', (elapsed, finished, total) => {
    expect(estimateRemainingMs(elapsed, finished, total)).toBeNull()
  })
})

describe('formatRemaining', () => {
  it.each([
    [4_000, 'a few seconds left'],
    [37_000, 'about 35 s left'],
    [58_000, 'about 1 min left'],
    [200_000, 'about 3 min left'],
  ])('formats %i ms as %s', (ms, expected) => {
    expect(formatRemaining(ms)).toBe(expected)
  })
})
