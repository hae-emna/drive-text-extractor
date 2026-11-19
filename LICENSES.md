# Third-party licences

This project is released under the [MIT licence](LICENSE). This file lists everything it
depends on, the licence of each piece, and whether that piece may be used in a **closed-source
commercial product**.

Last checked on 2026-11-19 against the exact versions in `backend/uv.lock`,
`frontend/package-lock.json` and the Docker image (see [How this list was produced](#how-this-list-was-produced)).

## Summary

- **No GPL or AGPL code is linked into or bundled with the application.** Every library the
  application imports or bundles is permissive (MIT, BSD, Apache-2.0 and similar).
- Two **weak-copyleft** components are present, both used unmodified, which their licences allow
  in closed-source products:
  - `certifi` (MPL-2.0): a CA certificate bundle used by `httpx`.
  - `libfribidi0` (LGPL-2.1+): a Debian system library loaded dynamically at runtime.
- The licences that were a real risk for this project (PyMuPDF and Ghostscript under AGPL-3.0,
  Poppler under GPL) were [avoided by design](#alternatives-rejected-for-licence-reasons).
- Obligations that remain: keep the licence and NOTICE texts of the Apache-2.0 and BSD components
  when redistributing (the Docker image keeps them in `/usr/share/doc` and in each package's
  `dist-info/licenses`), and ship the notices of the JavaScript bundled into the web page (done at
  build time, see [Web page](#web-page-shipped-to-the-browser)).

**Commercial use** below means "can be used in a closed-source product sold commercially".

## Application, shipped in the Docker image

### Python packages imported by the backend

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| fastapi | 0.165.0 | MIT | Yes | HTTP framework |
| starlette | 1.10.0 | BSD-3-Clause | Yes | ASGI toolkit under FastAPI |
| uvicorn | 0.54.0 | BSD-3-Clause | Yes | ASGI server |
| pydantic | 2.14.4 | MIT | Yes | Validation, response schemas |
| pydantic-core | 2.50.5 | MIT | Yes | |
| pydantic-settings | 2.16.3 | MIT | Yes | Settings from environment |
| httpx | 0.28.1 | BSD-3-Clause | Yes | Google Drive API client |
| **pypdfium2** | 5.15.2 | Apache-2.0 or BSD-3-Clause | Yes | PDF text layer and page rendering. Bundles PDFium, see below |
| **pytesseract** | 0.3.13 | Apache-2.0 | Yes | Runs the Tesseract binary in a subprocess |
| **pillow** | 13.0.0 | MIT-CMU (HPND) | Yes | Image preparation for OCR. Bundles codecs, see below |

### Transitive Python packages

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| annotated-doc | 0.0.7 | MIT | Yes | |
| annotated-types | 0.8.0 | MIT | Yes | |
| anyio | 4.16.0 | MIT | Yes | |
| certifi | 2026.10.23 | MPL-2.0 | Yes | Weak copyleft at file level; used unmodified. Changes to its own files would have to be published |
| click | 8.5.1 | BSD-3-Clause | Yes | |
| h11 | 0.16.0 | MIT | Yes | |
| httpcore | 1.0.9 | BSD-3-Clause | Yes | |
| idna | 3.20 | BSD-3-Clause | Yes | |
| opentelemetry-api | 1.45.2 | Apache-2.0 | Yes | Pulled in by FastAPI |
| packaging | 26.3 | Apache-2.0 or BSD-2-Clause | Yes | |
| python-dotenv | 1.2.4 | BSD-3-Clause | Yes | `.env` support in pydantic-settings |
| typing-extensions | 4.16.0 | PSF-2.0 | Yes | |
| typing-inspection | 0.4.5 | MIT | Yes | |

### Native libraries bundled inside Python wheels

| Component | Inside | Licence | Commercial use | Note |
|---|---|---|---|---|
| PDFium (pdfium-binaries build) | pypdfium2 | BSD-3-Clause / Apache-2.0 | Yes | The wheel ships the licences of PDFium's own dependencies in `dist-info/licenses/BUILD_LICENSES`: FreeType (FTL), libjpeg-turbo (IJG, BSD-3), OpenJPEG (BSD-2), lcms2 (MIT), libpng, libtiff, zlib, abseil (Apache-2.0), ICU (Unicode), AGG 2.3, fast_float, simdutf, highway and dragonbox (all permissive) |
| FreeType 2.14 | pillow | FTL (dual FTL / GPL-2.0; the FTL option is taken) | Yes | FTL requires a credit in the documentation: *Portions of this software are copyright © The FreeType Project (www.freetype.org). All rights reserved.* |
| HarfBuzz, raqm | pillow | MIT | Yes | Text shaping |
| libjpeg-turbo | pillow | IJG, BSD-3-Clause, zlib | Yes | |
| libpng, zlib, libtiff, libwebp, libavif, lcms2, OpenJPEG, brotli, zstd, liblzma, libxcb | pillow | Permissive (libpng, zlib, libtiff, BSD, MIT, 0BSD) | Yes | Listed in the wheel's SBOM (`dist-info/sboms`) |
| libimagequant | — | GPL-3.0+ | n/a | **Not present.** Pillow's SBOM mentions it as an optional component, but `PIL.features.check_feature("libimagequant")` is `False` in both the Linux image and the Windows development wheel |

### System packages in the Docker image (Debian 13, `python:3.13-slim`)

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| **Tesseract OCR** | 5.5.0 | Apache-2.0 | Yes | OCR engine, run as a separate process |
| Tesseract language data `eng`, `fra`, `ara`, `osd` | 4.1.0 | Apache-2.0 | Yes | `tessdata_fast` models packaged by Debian |
| Leptonica | 1.84.1 | BSD-2-Clause (Leptonica licence) | Yes | Image library used by Tesseract |
| libfribidi0 | 1.0.16 | LGPL-2.1-or-later | Yes | System library pulled in by Debian's `tesseract-ocr` package (through Pango), also loaded at runtime by Pillow's raqm. Used unmodified and replaceable, which satisfies the LGPL |
| CPython | 3.13.18 | PSF-2.0 | Yes | |
| Debian base system | 13 | Mixed: mostly permissive; some GPL tools (bash, coreutils...) | Yes | Separate programs aggregated in the image, not linked with the application. Anyone redistributing the image must be able to point to their sources, which Debian publishes |

### Web page, shipped to the browser

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| react | 19.3.1 | MIT | Yes | |
| react-dom | 19.3.1 | MIT | Yes | |
| scheduler | 0.28.0 | MIT | Yes | Dependency of react-dom |
| Tailwind CSS (generated CSS) | 4.3.5 | MIT | Yes | The compiled stylesheet contains Tailwind's base styles |

Minification removes licence comments, so the build writes `third-party-licenses.md` next to the
bundle (Vite `build.license`) and the page footer links to it.

### Sample files

The files in `samples/input` are generated by this project and are covered by its MIT licence.
`backend/scripts/make_samples.py` draws text with the DejaVu Sans font (Bitstream Vera / DejaVu
licence, permissive) inside the test image; the font is not part of the runtime image.

## Build and development tools, not distributed

These run on developer machines and in CI only. None of their code ends up in the image or the
web page (apart from the Tailwind CSS listed above).

| Tool | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| uv | 0.13.9 | MIT or Apache-2.0 | Yes | Python dependency manager; also copied into the image's build stages |
| pytest | 9.2.0 | MIT | Yes | |
| ruff | 0.17.5 | MIT | Yes | Lint and format |
| mypy | 2.4.1 | MIT | Yes | Type checking |
| pre-commit, pre-commit-hooks | 4.7.0, 6.0.0 | MIT | Yes | Git hooks |
| conventional-pre-commit | 4.5.0 | Apache-2.0 | Yes | Commit message check |
| Node.js | 24 | MIT | Yes | Build stage only (`node:24-alpine`) |
| vite, @vitejs/plugin-react | 8.3.8, 6.3.0 | MIT | Yes | |
| typescript | 7.0.2 | Apache-2.0 | Yes | |
| tailwindcss, @tailwindcss/vite | 4.3.5 | MIT | Yes | |
| lightningcss | (via Tailwind) | MPL-2.0 | Yes | CSS processor run at build time; its output is not covered by the MPL |
| oxlint | 1.94.0 | MIT | Yes | |
| prettier | 3.10.1 | MIT | Yes | |
| vitest, jsdom | 5.1.1, 29.1.1 | MIT | Yes | |
| @testing-library/react, jest-dom, user-event | 16.3.3, 8.0.0, 14.6.13 | MIT | Yes | |

The whole npm lockfile (208 packages) contains only MIT, ISC, BSD, Apache-2.0, 0BSD, MIT-0,
BlueOak-1.0.0, CC0-1.0 and, for `lightningcss` only, MPL-2.0.

## Alternatives rejected for licence reasons

| Candidate | Licence | Why it was not used | Chosen instead |
|---|---|---|---|
| PyMuPDF (fitz) | AGPL-3.0 (or a paid commercial licence) | AGPL would force the whole service, network use included, to be published under the AGPL | pypdfium2 (Apache-2.0 / BSD-3) |
| pdf2image | MIT, but requires Poppler | Poppler is GPL-2.0/3.0 and would be a required runtime dependency | Page rendering with pypdfium2 |
| pdftotext / poppler-utils | GPL-2.0 | Same as above | pypdfium2 text layer |
| OCRmyPDF | MPL-2.0, but requires Ghostscript | Ghostscript is AGPL-3.0 | Own scanned-page fallback: pypdfium2 rendering + Tesseract |
| OpenCV (opencv-python) | Apache-2.0, but wheels bundle FFmpeg (LGPL) and, for the GUI build, Qt (LGPL) | Licence-compatible, but the bundled LGPL codecs add obligations for no real gain (only deskewing was needed) | Pillow preprocessing + Tesseract orientation detection |

Considered for other reasons, licence-compatible: `pdfplumber` (MIT, redundant with pypdfium2),
`EasyOCR` / `PaddleOCR` (Apache-2.0, heavy deep-learning stacks; a candidate for better Arabic
OCR later), paid cloud OCR APIs (not open source or self-hostable; could be added as an optional
`OcrEngine` implementation), `gdown` (MIT, scrapes Drive's web pages instead of using the API).

## How this list was produced

```bash
# Python runtime packages and their declared licences
cd backend
uv export --no-dev --no-hashes --format requirements-txt
uv run python -c "import importlib.metadata as m; print(m.metadata('pypdfium2')['License-Expression'])"

# Libraries bundled inside wheels, and the system packages, inside the built image
docker build --target runtime -t drive-text-extractor .
docker run --rm --entrypoint bash drive-text-extractor -c \
  "ls /opt/venv/lib/python3.13/site-packages/pillow.libs; dpkg -l | grep -E 'tesseract|leptonica|fribidi'"
#   Pillow:    dist-info/sboms/*.cdx.json and PIL.features.check_feature(...)
#   pypdfium2: dist-info/licenses/BUILD_LICENSES

# npm packages: the "license" field of every entry in frontend/package-lock.json
```

Re-run these checks whenever `uv.lock`, `package-lock.json` or the Dockerfile changes.
