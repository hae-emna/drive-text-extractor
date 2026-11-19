import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { driveFile, result } from '../../test/fixtures'
import { ResultCard } from './ResultCard'

const SCAN = driveFile({
  id: 's',
  name: 'scan.png',
  path: 'archive/scan.png',
  mime_type: 'image/png',
})
const ARABIC_AND_FRENCH = 'فاتورة رقم 12\nFacture n° 12'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ResultCard', () => {
  it('shows the method, confidence and text of a finished file', () => {
    render(
      <ResultCard
        result={result(SCAN, {
          status: 'done',
          method: 'ocr',
          mean_confidence: 91.4,
          char_count: ARABIC_AND_FRENCH.length,
          duration_ms: 1840,
          text: ARABIC_AND_FRENCH,
        })}
      />,
    )

    expect(screen.getByRole('heading', { name: 'archive/scan.png' })).toBeInTheDocument()
    expect(screen.getByText('OCR')).toBeInTheDocument()
    expect(screen.getByText('OCR confidence 91%')).toBeInTheDocument()
    expect(screen.getByText('1.8 s')).toBeInTheDocument()
    expect(screen.getByText(/Facture/)).toHaveAttribute('dir', 'auto')
    expect(screen.queryByText(/Low OCR confidence/)).not.toBeInTheDocument()
  })

  it('flags low-confidence OCR', () => {
    render(
      <ResultCard
        result={result(SCAN, {
          status: 'done',
          method: 'ocr',
          mean_confidence: 41,
          low_confidence: true,
          text: 'blurry',
        })}
      />,
    )

    expect(screen.getByText(/Low OCR confidence/)).toBeInTheDocument()
  })

  it('explains how a mixed PDF was read', () => {
    const pdf = driveFile({ id: 'p', name: 'contract.pdf' })
    render(
      <ResultCard
        result={result(pdf, {
          status: 'done',
          method: 'mixed',
          text: 'typed and scanned',
          pages: [
            { number: 1, method: 'pdf_parser', confidence: null, text: 'typed' },
            { number: 2, method: 'ocr', confidence: 80, text: 'scanned' },
          ],
        })}
      />,
    )

    expect(screen.getByText('PDF parser + OCR')).toBeInTheDocument()
    expect(screen.getByText('1 page of 2 read with OCR')).toBeInTheDocument()
  })

  it('shows why a file failed', () => {
    render(
      <ResultCard
        result={result(SCAN, {
          status: 'failed',
          error: { code: 'corrupt_file', message: 'This file is damaged.' },
        })}
      />,
    )

    expect(screen.getByText(/This file is damaged\./)).toBeInTheDocument()
    expect(screen.getByText('(corrupt_file)')).toBeInTheDocument()
  })

  it('says so when a file has no text', () => {
    render(<ResultCard result={result(SCAN, { status: 'done', method: 'ocr', text: '' })} />)

    expect(screen.getByText('No text was found in this file.')).toBeInTheDocument()
  })

  it('copies the text to the clipboard', async () => {
    // user-event installs its own clipboard on setup(); spy on that one.
    const user = userEvent.setup()
    const writeText = vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue(undefined)
    render(<ResultCard result={result(SCAN, { status: 'done', method: 'ocr', text: 'hello' })} />)

    await user.click(screen.getByRole('button', { name: 'Copy text of scan.png' }))

    expect(writeText).toHaveBeenCalledWith('hello')
    expect(await screen.findByText('Copied')).toBeInTheDocument()
  })

  it('collapses long texts behind a toggle', async () => {
    const user = userEvent.setup()
    const long = 'x'.repeat(5000)
    render(<ResultCard result={result(SCAN, { status: 'done', method: 'ocr', text: long })} />)
    const toggle = screen.getByRole('button', { name: 'Show all 5,000 characters' })

    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    await user.click(toggle)
    expect(screen.getByRole('button', { name: 'Show less' })).toHaveAttribute(
      'aria-expanded',
      'true',
    )
  })

  it('tells a queued file from one being read', () => {
    const { rerender } = render(<ResultCard result={result(SCAN, { status: 'pending' })} />)

    expect(screen.getByRole('article')).toHaveAttribute('aria-busy', 'true')
    expect(screen.getByText(/Waiting for a free slot/)).toBeInTheDocument()

    rerender(<ResultCard result={result(SCAN, { status: 'processing' })} />)

    expect(screen.getByText('Downloading and extracting text…')).toBeInTheDocument()
    expect(screen.queryByText(/Waiting for a free slot/)).not.toBeInTheDocument()
  })
})
