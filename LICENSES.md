# Third-party licences

This project is released under the [MIT licence](LICENSE). Every component it ships may be used
in a closed-source commercial product. None of it is GPL or AGPL, apart from GCC's Fortran
runtime inside the OpenCV and NumPy wheels, which the GCC Runtime Library Exception lets any
program use.

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
| RapidOCR | Apache-2.0 | Yes | OCR for photos and screenshots |
| ONNX Runtime | MIT | Yes | Runs the OCR models |
| OpenCV, headless build | Apache-2.0 | Yes | Image operations of RapidOCR's text detector |
| PP-OCRv5 models (PaddleOCR, converted to ONNX by RapidOCR) | Apache-2.0 | Yes | Text detection, line orientation and Latin recognition, baked into the image |
| React, React DOM | MIT | Yes | Web page |
| Tailwind CSS | MIT | Yes | Styles |

Transitive dependencies are permissive (MIT, BSD, Apache-2.0, PSF-2.0), with weak-copyleft
exceptions, all used unmodified, which their licences allow in commercial products:

- `certifi` (MPL-2.0, the CA bundle used by httpx and requests) and `tqdm` (MPL-2.0 and MIT,
  pulled in by RapidOCR).
- Debian's `libfribidi0` (LGPL-2.1+, installed with Tesseract).
- FFmpeg and libquadmath inside the OpenCV wheel, and GEOS inside the shapely wheel
  (LGPL-2.1+). They are shared libraries loaded at runtime, which a user can replace, as the
  LGPL requires.

Build and test tools (uv, pytest, ruff, mypy, Vite, TypeScript, Vitest, oxlint, Prettier) are
MIT or Apache-2.0 and are not shipped. `lightningcss`, which Tailwind runs at build time, is
MPL-2.0; its output is not covered by the MPL.

## Notices

- Pillow bundles FreeType under the FreeType Licence, which asks for this credit: *Portions of this
  software are copyright © The FreeType Project (www.freetype.org). All rights reserved.*
- The OCR models are copyright Baidu and the PaddleOCR authors. RapidOCR's `MODEL_LICENSES.md`
  asks redistributors to keep this attribution: *converted from an official PaddleOCR model to
  the ONNX format and packaged for use with RapidOCR; the upstream model weights are copyright
  Baidu and/or the applicable PaddleOCR rights holders and are licensed under the Apache License,
  Version 2.0.*
- The licence and NOTICE texts of the Python packages stay in the Docker image, in each package's
  `dist-info`, and in `/usr/share/doc/*/copyright` for Debian packages.
- Minification strips licence comments from the web page, so the build writes
  `third-party-licenses.md` next to the bundle and the page footer links to it.

## Rejected for licence reasons

| Candidate | Licence | Problem | Used instead |
|---|---|---|---|
| PyMuPDF | AGPL-3.0 | Would put the whole service, network use included, under the AGPL | pypdfium2 |
| pdf2image, pdftotext | Need Poppler (GPL) | GPL runtime dependency | pypdfium2 |
| OCRmyPDF | MPL-2.0, needs Ghostscript (AGPL-3.0) | Same problem as PyMuPDF | pypdfium2 + Tesseract |
| OpenCV, GUI build (opencv-python) | Apache-2.0, bundles Qt (LGPL) on top of FFmpeg | Not needed: RapidOCR only needs the headless build | opencv-python-headless |
| RapidOCR's Arabic model | Apache-2.0, needs `python-bidi` (LGPL-3.0) for right-to-left output | One more LGPL component for a path Tesseract already covers | Tesseract when Arabic is selected |
