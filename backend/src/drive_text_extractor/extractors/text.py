"""Text clean-up shared by every extraction method."""

import re
import unicodedata

_TRAILING_SPACES = re.compile(r"[ \t]+\n")
_EXTRA_BLANK_LINES = re.compile(r"\n{3,}")


def normalize_text(raw: str) -> str:
    """Make extracted text comparable whatever engine produced it.

    - NFKC folds compatibility characters: Arabic presentation forms (common in PDFs) become
      regular Arabic letters, ligatures such as U+FB01 become "fi", full-width digits become ASCII.
    - Newlines are unified, trailing spaces and runs of blank lines are removed.
    - Control characters are dropped, but format characters (e.g. the zero-width non-joiner used
      in Arabic-script text) are kept.
    """
    text = unicodedata.normalize("NFKC", raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch) != "Cc")
    text = _TRAILING_SPACES.sub("\n", text)
    text = _EXTRA_BLANK_LINES.sub("\n\n", text)
    return text.strip()
