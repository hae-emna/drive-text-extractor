import { describe, expect, it } from 'vitest'
import { DEFAULT_LANGUAGES, usableLanguages } from './languages'

const without = (code: string) =>
  DEFAULT_LANGUAGES.map((language) => ({ ...language, installed: language.code !== code }))

describe('usableLanguages', () => {
  it('keeps the chosen languages that are installed', () => {
    expect(usableLanguages(['eng', 'fra'], DEFAULT_LANGUAGES)).toEqual(['eng', 'fra'])
  })

  it('drops a chosen language whose pack is missing', () => {
    expect(usableLanguages(['eng', 'fra'], without('fra'))).toEqual(['eng'])
  })

  it('falls back to the first installed language when none of the chosen ones is', () => {
    expect(usableLanguages(['eng'], without('eng'))).toEqual(['fra'])
  })
})
