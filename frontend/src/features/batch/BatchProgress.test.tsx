import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { FileStatus } from '../../api/types'
import { driveFile, job, result } from '../../test/fixtures'
import { BatchProgress } from './BatchProgress'

function jobWith(statuses: FileStatus[]) {
  return job(
    statuses.map((status, index) =>
      result(driveFile({ id: `f-${index}`, name: `file-${index}.pdf` }), { status }),
    ),
  )
}

describe('BatchProgress', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('breaks the batch down by status', () => {
    render(
      <BatchProgress
        job={jobWith(['done', 'failed', 'processing', 'pending', 'pending'])}
        onCancel={() => {}}
      />,
    )

    expect(screen.getByText('Processing… 2 of 5 files')).toBeInTheDocument()
    for (const text of ['1 done', '1 failed', '1 processing', '2 waiting']) {
      expect(screen.getByText(text)).toBeInTheDocument()
    }
    expect(screen.queryByText(/cancelled/)).not.toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'Batch progress' })).toHaveAttribute(
      'aria-valuetext',
      '2 of 5 files finished',
    )
  })

  it('names the files being read', () => {
    render(
      <BatchProgress
        job={jobWith(['processing', 'processing', 'processing', 'processing', 'pending'])}
        onCancel={() => {}}
      />,
    )

    expect(screen.getByText('Reading file-0.pdf, file-1.pdf, file-2.pdf and 1 more')).toBeVisible()
  })

  it('counts the time spent and estimates the time left once a file has finished', () => {
    const { rerender } = render(
      <BatchProgress job={jobWith(['processing', 'pending', 'pending'])} onCancel={() => {}} />,
    )
    act(() => vi.advanceTimersByTime(10_000))

    expect(screen.getByText('10 s elapsed')).toBeInTheDocument()

    rerender(<BatchProgress job={jobWith(['done', 'processing', 'pending'])} onCancel={() => {}} />)

    // One file in 10 s, two to go.
    expect(screen.getByText('10 s elapsed · about 20 s left')).toBeInTheDocument()
  })

  it('reports the total time of a finished batch from the server clock', () => {
    const finished = { ...jobWith(['done', 'done']), finished_at: '2026-11-19T09:01:05Z' }
    render(<BatchProgress job={finished} onCancel={() => {}} />)

    expect(screen.getByText('Finished: 2 files')).toBeInTheDocument()
    expect(screen.getByText('in 1 min 05 s')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument()
  })
})
