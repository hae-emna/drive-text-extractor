import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'
import type { Language, LanguageCode } from '../../api/types'
import { DEFAULT_LANGUAGES } from './languages'
import { LanguagePicker } from './LanguagePicker'

function Harness({ languages = DEFAULT_LANGUAGES }: { languages?: Language[] }) {
  const [value, setValue] = useState<LanguageCode[]>(['eng'])
  return (
    <>
      <LanguagePicker languages={languages} value={value} onChange={setValue} />
      <output>{value.join('+')}</output>
    </>
  )
}

describe('LanguagePicker', () => {
  it('keeps the canonical order whatever the click order', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByLabelText('Arabic'))
    await user.click(screen.getByLabelText('French'))

    expect(screen.getByRole('status')).toHaveTextContent('eng+fra+ara')
  })

  it('never lets the last language be unchecked', () => {
    render(<Harness />)

    expect(screen.getByLabelText('English')).toBeDisabled()
  })

  it('disables languages whose pack is not installed', () => {
    const languages = DEFAULT_LANGUAGES.map((language) => ({
      ...language,
      installed: language.code !== 'ara',
    }))
    render(<Harness languages={languages} />)

    expect(screen.getByLabelText('Arabic')).toBeDisabled()
    expect(screen.getByLabelText('French')).toBeEnabled()
  })
})
