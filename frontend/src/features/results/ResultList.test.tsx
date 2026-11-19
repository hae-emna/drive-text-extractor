import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { job, LISTING, result } from '../../test/fixtures'
import { ResultList } from './ResultList'

const [pdf, png] = LISTING.files as [(typeof LISTING.files)[0], (typeof LISTING.files)[0]]

describe('ResultList', () => {
  it('offers the JSON export once the batch has finished', () => {
    const finished = job([result(pdf, { status: 'done', method: 'pdf_parser', text: 'a' })])
    render(<ResultList job={finished} onSelectFailed={() => {}} />)

    expect(screen.getByRole('link', { name: 'Export JSON' })).toHaveAttribute(
      'href',
      '/api/jobs/job-1/export',
    )
  })

  it('keeps the export disabled while the batch runs', () => {
    const running = job([result(pdf, { status: 'processing' })])
    render(<ResultList job={running} onSelectFailed={() => {}} />)

    expect(screen.getByRole('button', { name: 'Export JSON' })).toBeDisabled()
  })

  it('selects the failed files for a retry', async () => {
    const onSelectFailed = vi.fn()
    const finished = job([
      result(pdf, { status: 'done', method: 'pdf_parser', text: 'a' }),
      result(png, { status: 'failed', error: { code: 'ocr_timeout', message: 'Too slow.' } }),
    ])
    render(<ResultList job={finished} onSelectFailed={onSelectFailed} />)

    await userEvent.click(screen.getByRole('button', { name: 'Select failed files to retry' }))

    expect(onSelectFailed).toHaveBeenCalledWith(['png-1'])
  })
})
