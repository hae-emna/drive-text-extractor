# syntax=docker/dockerfile:1

# --- 1. Build the web page ------------------------------------------------------------------
FROM node:24-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- 2. Python with Tesseract and the locked dependencies -----------------------------------
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
# tesseract-ocr pulls in the English and orientation (osd) models; French and Arabic are added.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-fra tesseract-ocr-ara \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv
WORKDIR /app
# Every "uv sync" mounts uv's download cache instead of leaving it in a layer (it would add the
# size of every wheel to the image a second time).
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project
# RapidOCR's models (about 14 MB) are fetched now, not on first use: the app runs as a user that
# cannot write to the package folder, and needs no network at run time. The script imports
# nothing else from the app, so this layer is rebuilt only when the choice of models changes.
ENV OCR_MODELS_DIR=/opt/ocr-models
COPY backend/src/drive_text_extractor/ocr/rapid_models.py /tmp/rapid_models.py
RUN python /tmp/rapid_models.py "$OCR_MODELS_DIR" && rm /tmp/rapid_models.py

# --- 3. Test image: docker build --target test -t dte-test . && docker run --rm dte-test ----
FROM base AS test
# DejaVu provides the Arabic glyphs scripts/make_samples.py needs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-install-project
COPY backend/ ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked
CMD ["pytest"]

# --- 4. Runtime image -----------------------------------------------------------------------
FROM base AS runtime
COPY backend/src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-editable && rm -rf ./src
COPY --from=web /web/dist ./static
COPY samples/input ./samples/input
ENV STATIC_DIR=/app/static \
    LOCAL_FOLDER=/app/samples/input
RUN useradd --system --uid 10001 --no-create-home app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"]
CMD ["uvicorn", "drive_text_extractor.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
