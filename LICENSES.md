# Third-party licences

This project is released under the [MIT licence](LICENSE). This file lists everything it
depends on, the licence of each piece, and whether that piece may be used in a **closed-source
commercial product**.

Last checked on 2026-11-19 against the exact versions in `backend/uv.lock`,
`frontend/package-lock.json` and the Docker image (see [How this list was produced](#how-this-list-was-produced)).

## Summary

- **No GPL or AGPL code is linked into or bundled with the application**, apart from GCC's
  Fortran runtime inside the OpenCV and NumPy wheels, whose GCC Runtime Library Exception allows
  it in any program. Every library the application imports is permissive (MIT, BSD, Apache-2.0 and
  similar).
- A few **weak-copyleft** components are present, all used unmodified, which their licences
  allow in closed-source products:
  - `certifi` (MPL-2.0): a CA certificate bundle used by `httpx` and `requests`.
  - `tqdm` (MPL-2.0 and MIT): progress bars, pulled in by RapidOCR.
  - `libfribidi0` (LGPL-2.1+): a Debian system library loaded dynamically at runtime.
  - FFmpeg and libquadmath (LGPL-2.1+) inside the `opencv-python-headless` wheel, and GEOS
    (LGPL-2.1) inside the `shapely` wheel: shared libraries loaded at runtime, which a user can
    replace, as the LGPL requires.
- The OCR models (PaddleOCR's PP-OCRv5, converted to ONNX by RapidOCR) are **Apache-2.0**.
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
| **rapidocr** | 3.10.0 | Apache-2.0 | Yes | OCR for photos and screenshots. Its wheel also ships `MODEL_LICENSES.md` |
| **onnxruntime** | 1.32.0 | MIT | Yes | Runs the OCR models. Third-party notices in the wheel (`ThirdPartyNotices.txt`) |

### Transitive Python packages

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| annotated-doc | 0.0.7 | MIT | Yes | |
| annotated-types | 0.8.0 | MIT | Yes | |
| anyio | 4.16.0 | MIT | Yes | |
| certifi | 2026.10.23 | MPL-2.0 | Yes | Weak copyleft at file level; used unmodified. Changes to its own files would have to be published |
| charset-normalizer | 3.5.2 | MIT | Yes | Through requests |
| colorlog | 6.12.0 | MIT | Yes | Through rapidocr |
| flatbuffers | 25.12.19 | Apache-2.0 | Yes | Through onnxruntime |
| numpy | 2.5.5 | BSD-3-Clause (and 0BSD, MIT, Zlib, CC0 for parts) | Yes | Through rapidocr and onnxruntime. Bundles OpenBLAS, see below |
| omegaconf | 2.4.0 | BSD-3-Clause | Yes | RapidOCR's configuration |
| **opencv-python-headless** | 5.1.0.95 | Apache-2.0 | Yes | Through rapidocr (image operations of the text detector). Bundles native libraries, see below |
| protobuf | 7.36.2 | BSD-3-Clause | Yes | Through onnxruntime |
| pyclipper | 1.4.0 | MIT (Clipper: Boost Software Licence) | Yes | Through rapidocr |
| pyyaml | 6.0.3 | MIT | Yes | Through omegaconf |
| requests | 2.34.2 | Apache-2.0 | Yes | Through rapidocr (model download) |
| shapely | 2.2.0 | BSD-3-Clause | Yes | Through rapidocr. Bundles GEOS, see below |
| six | 1.17.0 | MIT | Yes | |
| tqdm | 4.70.1 | MPL-2.0 and MIT | Yes | Through rapidocr. Same MPL-2.0 terms as certifi; used unmodified |
| urllib3 | 2.8.0 | MIT | Yes | Through requests |
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
| FFmpeg (libavcodec, libavformat, libavutil, libswscale, libswresample) | opencv-python-headless | LGPL-2.1-or-later | Yes | Video I/O, never called by this project. Shared libraries in `opencv_python_headless.libs`, used unmodified and replaceable, which satisfies the LGPL. Licence text in the wheel's `LICENSE-3RD-PARTY.txt` |
| libquadmath | opencv-python-headless | LGPL-2.1-or-later | Yes | GCC's quad-precision maths library, same terms as FFmpeg |
| libgfortran | opencv-python-headless | GPL-3.0+ with the GCC Runtime Library Exception | Yes | The exception lets the runtime be combined with programs under any licence |
| libvpx, libaom, dav1d, libavif, libpng, OpenBLAS | opencv-python-headless | BSD-3-Clause, BSD-2-Clause, libpng | Yes | Listed in the wheel's `LICENSE-3RD-PARTY.txt` and SBOM |
| GEOS 3.14 | shapely | LGPL-2.1 | Yes | Geometry library, shared libraries in `shapely.libs`; same terms as FFmpeg |
| OpenBLAS (scipy-openblas) | numpy | BSD-3-Clause | Yes | numpy documents the GCC runtime pieces linked into it in its bundled licence notes, under the same exception as above |

### OCR models in the Docker image

Fetched at build time into `/opt/ocr-models` (`backend/src/drive_text_extractor/ocr/rapid_models.py`),
about 14 MB:

| Model | Licence | Commercial use | Note |
|---|---|---|---|
| `ch_PP-OCRv5_det_mobile` (text detection) | Apache-2.0 | Yes | PaddleOCR model, converted to ONNX by RapidOCR |
| `ch_PP-LCNet_x0_25_textline_ori_cls_mobile` (line orientation) | Apache-2.0 | Yes | Same |
| `latin_PP-OCRv5_rec_mobile` (recognition, Latin scripts) | Apache-2.0 | Yes | Same |

The weights are copyright Baidu and the PaddleOCR authors. RapidOCR's `MODEL_LICENSES.md`
(shipped in the image, in the `rapidocr` dist-info) records their provenance and the attribution
to keep when redistributing: *converted from an official PaddleOCR model to the ONNX format and
packaged for use with RapidOCR; the upstream model weights are copyright Baidu and/or the
applicable PaddleOCR rights holders and are licensed under the Apache License, Version 2.0.*

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
| OpenCV, GUI build (opencv-python) | Apache-2.0, but bundles Qt (LGPL) on top of FFmpeg | Not needed: RapidOCR only needs the headless build | `opencv-python-headless`, pulled in by RapidOCR |
| RapidOCR's Arabic model | Apache-2.0, but needs `python-bidi` (LGPL-3.0) for right-to-left output | One more LGPL component for a path Tesseract already covers | Tesseract for images when Arabic is selected |

OpenCV itself was first rejected too, when it would only have served for deskewing. It came in
with RapidOCR, which needs it and brings a large accuracy gain on photos; only the headless build,
without Qt, is installed.

Considered for other reasons, licence-compatible: `pdfplumber` (MIT, redundant with pypdfium2),
`EasyOCR` (Apache-2.0, on PyTorch: far heavier than ONNX Runtime) and `PaddleOCR` itself
(Apache-2.0, needs the PaddlePaddle runtime; RapidOCR runs the same models on ONNX Runtime),
paid cloud OCR APIs (not open source or self-hostable; could be added as an optional `OcrEngine`
implementation), `gdown` (MIT, scrapes Drive's web pages instead of using the API).

## How this list was produced

```bash
# Python runtime packages and their declared licences
cd backend
uv export --no-dev --no-hashes --format requirements-txt
uv run python -c "import importlib.metadata as m; print(m.metadata('pypdfium2')['License-Expression'])"

# Libraries bundled inside wheels, and the system packages, inside the built image
docker build --target runtime -t drive-text-extractor .
docker run --rm --entrypoint bash drive-text-extractor -c \
  "cd /opt/venv/lib/python3.13/site-packages && ls pillow.libs opencv_python_headless.libs shapely.libs numpy.libs; dpkg -l | grep -E 'tesseract|leptonica|fribidi'"
#   Pillow:    dist-info/sboms/*.cdx.json and PIL.features.check_feature(...)
#   pypdfium2: dist-info/licenses/BUILD_LICENSES
#   OpenCV:    opencv_python_headless-*.dist-info/LICENSE-3RD-PARTY.txt and sboms/
#   Models:    rapidocr-*.dist-info/licenses/MODEL_LICENSES.md and rapidocr/default_models.yaml

# npm packages: the "license" field of every entry in frontend/package-lock.json
```

Re-run these checks whenever `uv.lock`, `package-lock.json` or the Dockerfile changes.
