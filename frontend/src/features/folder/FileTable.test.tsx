import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'
import { LISTING } from '../../test/fixtures'
import { FileTable } from './FileTable'
import { toggle, toggleAll } from './selection'

function Harness() {
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set())
  const ids = LISTING.files.map((file) => file.id)
  return (
    <FileTable
      files={LISTING.files}
      selected={selected}
      onToggle={(id) => setSelected((current) => toggle(current, id))}
      onToggleAll={() => setSelected((current) => toggleAll(current, ids))}
    />
  )
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
})
