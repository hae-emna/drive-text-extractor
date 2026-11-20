import type { Language, LanguageCode } from '../../api/types'

/** Offered until the server reports which language packs it actually has. */
export const DEFAULT_LANGUAGES: Language[] = [
  { code: 'eng', name: 'English', installed: true },
  { code: 'fra', name: 'French', installed: true },
  { code: 'ara', name: 'Arabic', installed: true },
]

/**
 * The chosen languages the server can actually use. A default such as French stays out of the
 * request, and unticked in the picker, when its pack is not installed; with nothing left, the
 * first installed language is used.
 */
export function usableLanguages(
  chosen: readonly LanguageCode[],
  offered: readonly Language[],
): LanguageCode[] {
  const installed = offered
    .filter((language) => language.installed)
    .map((language) => language.code)
  const usable = chosen.filter((code) => installed.includes(code))
  return usable.length > 0 ? usable : installed.slice(0, 1)
}
