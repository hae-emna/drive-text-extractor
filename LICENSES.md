# Third-party licences

This project is released under the [MIT licence](LICENSE). Every component it ships may be used
in a closed-source commercial product, and none of it is GPL or AGPL.

## Runtime dependencies

| Dependency | Licence | Commercial use | Used for |
|---|---|---|---|
| FastAPI | MIT | Yes | HTTP API |
| Uvicorn | BSD-3-Clause | Yes | ASGI server |
| Pydantic, pydantic-settings | MIT | Yes | Validation and settings |
| httpx | BSD-3-Clause | Yes | Google Drive API client |
| pypdfium2 (PDFium) | Apache-2.0 or BSD-3-Clause | Yes | PDF text layer and page rendering |
| pytesseract | Apache-2.0 | Yes | Python wrapper around Tesseract |
| Tesseract OCR 5 | Apache-2.0 | Yes | OCR engine, run as a separate process |
| Pillow | MIT-CMU (HPND) | Yes | Image preparation for OCR |
| React, React DOM | MIT | Yes | Web page |
| Tailwind CSS | MIT | Yes | Styles |

Transitive dependencies are permissive (MIT, BSD, Apache-2.0, PSF-2.0), with two weak-copyleft
exceptions, both used unmodified, which their licences allow in commercial products: `certifi`
(MPL-2.0, the CA bundle used by httpx) and Debian's `libfribidi0` (LGPL-2.1+, installed with
Tesseract).

Build and test tools (uv, pytest, ruff, mypy, Vite, TypeScript, Vitest, oxlint, Prettier) are
MIT or Apache-2.0 and are not shipped.

## Rejected for licence reasons

| Candidate | Licence | Problem | Used instead |
|---|---|---|---|
| PyMuPDF | AGPL-3.0 | Would put the whole service, network use included, under the AGPL | pypdfium2 |
| pdf2image, pdftotext | Need Poppler (GPL) | GPL runtime dependency | pypdfium2 |
| OCRmyPDF | MPL-2.0, needs Ghostscript (AGPL-3.0) | Same problem as PyMuPDF | pypdfium2 + Tesseract |
