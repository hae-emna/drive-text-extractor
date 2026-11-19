import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'
import type { DriveFile } from '../../api/types'
import { driveFile, LISTING } from '../../test/fixtures'
import { FileTable } from './FileTable'

function Harness({ files = LISTING.files }: { files?: DriveFile[] }) {
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set())
  return (
    <>
      <FileTable files={files} selected={selected} onSelectionChange={setSelected} />
      <output>{selected.size} selected</output>
    </>
  )
}

const MANY = Array.from({ length: 60 }, (_, index) =>
  driveFile({ id: `f-${index + 1}`, name: `doc-${String(index + 1).padStart(2, '0')}.pdf` }),
)

function rowNames(): string[] {
  return screen
    .getAllByRole('checkbox', { name: /^Select doc-/ })
    .map((box) => box.getAttribute('aria-label')?.replace('Select ', '') ?? '')
}

describe('FileTable', () => {
  it('shows name, path, type and size of each file', () => {
    render(<Harness />)

    expect(screen.getByText('invoice.pdf')).toBeInTheDocument()
    expect(screen.getByText('archive/scan.jpg')).toBeInTheDocument()
    expect(screen.getByText('PNG')).toBeInTheDocument()
    expect(screen.getByText('2.4 MB')).toBeInTheDocument()
  })

  it('selects files one by one and shows a partial "select all"', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByRole('checkbox', { name: 'Select invoice.pdf' }))

    const selectAll = screen.getByRole<HTMLInputElement>('checkbox', { name: 'Select all files' })
    expect(screen.getByRole('checkbox', { name: 'Select invoice.pdf' })).toBeChecked()
    expect(selectAll.indeterminate).toBe(true)
    expect(selectAll).not.toBeChecked()
  })

  it('selects and clears everything with "select all"', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    const selectAll = screen.getByRole<HTMLInputElement>('checkbox', { name: 'Select all files' })

    await user.click(selectAll)
    expect(screen.getAllByRole('checkbox').every((box) => (box as HTMLInputElement).checked)).toBe(
      true,
    )
    expect(selectAll.indeterminate).toBe(false)

    await user.click(selectAll)
    expect(screen.getAllByRole('checkbox').some((box) => (box as HTMLInputElement).checked)).toBe(
      false,
    )
  })

  it('shows one page at a time and moves between pages', async () => {
    const user = userEvent.setup()
    render(<Harness files={MANY} />)
    const nav = screen.getByRole('navigation', { name: 'File pages' })

    expect(rowNames()).toHaveLength(25)
    expect(rowNames()[0]).toBe('doc-01.pdf')
    expect(within(nav).getByText(/Showing/)).toHaveTextContent('Showing 1–25 of 60 files')
    expect(within(nav).getByRole('button', { name: 'Previous page' })).toBeDisabled()

    await user.click(within(nav).getByRole('button', { name: 'Page 3' }))

    expect(rowNames()).toEqual(MANY.slice(50).map((file) => file.name))
    expect(within(nav).getByRole('button', { name: 'Page 3' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(within(nav).getByRole('button', { name: 'Next page' })).toBeDisabled()
  })

  it('keeps the first visible file on screen when the page size changes', async () => {
    const user = userEvent.setup()
    render(<Harness files={MANY} />)

    await user.click(screen.getByRole('button', { name: 'Page 2' }))
    await user.selectOptions(screen.getByLabelText('Per page'), '50')

    expect(rowNames()[0]).toBe('doc-01.pdf')
    expect(rowNames()).toHaveLength(50)
    expect(screen.getByText(/Showing/)).toHaveTextContent('Showing 1–50 of 60 files')
  })

  it('selects a page, or every file on every page', async () => {
    const user = userEvent.setup()
    render(<Harness files={MANY} />)

    await user.click(screen.getByRole('checkbox', { name: 'Select all files on this page' }))
    expect(screen.getByText('25 selected')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Select all' }))
    expect(screen.getByText('60 selected')).toBeInTheDocument()
    expect(screen.getByText('60 of 60 files selected')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Clear selection' }))
    expect(screen.getByText('0 selected')).toBeInTheDocument()
  })

  it('keeps selections made on other pages', async () => {
    const user = userEvent.setup()
    render(<Harness files={MANY} />)

    await user.click(screen.getByRole('checkbox', { name: 'Select doc-01.pdf' }))
    await user.click(screen.getByRole('button', { name: 'Next page' }))
    const pageBox = screen.getByRole('checkbox', { name: 'Select all files on this page' })
    await user.click(pageBox)
    await user.click(pageBox)

    expect(screen.getByText('1 selected')).toBeInTheDocument()
  })

  it('hides the page controls when every file fits on one page', () => {
    render(<Harness />)

    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
  })
})
