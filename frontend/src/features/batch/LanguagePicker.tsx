import type { Language, LanguageCode } from '../../api/types'

interface LanguagePickerProps {
  languages: Language[]
  value: readonly LanguageCode[]
  onChange: (value: LanguageCode[]) => void
  disabled?: boolean
}

export function LanguagePicker({
  languages,
  value,
  onChange,
  disabled = false,
}: LanguagePickerProps) {
  function toggle(code: LanguageCode) {
    const next = value.includes(code) ? value.filter((chosen) => chosen !== code) : [...value, code]
    // Keep the canonical order so the request does not depend on click order.
    onChange(
      languages
        .map((language) => language.code)
        .filter((languageCode) => next.includes(languageCode)),
    )
  }

  return (
    <fieldset disabled={disabled} className="flex flex-wrap items-center gap-2">
      <legend className="sr-only">OCR languages</legend>
      <span className="mr-1 text-sm font-medium" aria-hidden="true">
        OCR languages
      </span>
      {languages.map((language) => {
        const checked = value.includes(language.code)
        const isLastChecked = checked && value.length === 1
        return (
          <label
            key={language.code}
            title={language.installed ? undefined : 'Language pack not installed on the server'}
            className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-zinc-300 px-3 py-1 text-sm has-checked:border-lime-600 has-checked:bg-lime-50 has-disabled:cursor-not-allowed has-disabled:opacity-50 dark:border-zinc-700 dark:has-checked:border-lime-400 dark:has-checked:bg-lime-950"
          >
            <input
              type="checkbox"
              checked={checked}
              // At least one language must stay selected.
              disabled={!language.installed || isLastChecked}
              onChange={() => toggle(language.code)}
              className="size-4 accent-lime-600"
            />
            {language.name}
          </label>
        )
      })}
    </fieldset>
  )
}
