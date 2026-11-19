import type { Language } from '../../api/types'

/** Offered until the server reports which language packs it actually has. */
export const DEFAULT_LANGUAGES: Language[] = [
  { code: 'eng', name: 'English', installed: true },
  { code: 'fra', name: 'French', installed: true },
  { code: 'ara', name: 'Arabic', installed: true },
]
