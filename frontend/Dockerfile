# syntax=docker/dockerfile:1
# Web image: the built page, served by nginx, which also forwards /api to the API container.
#   docker build -t drive-text-extractor-web frontend

# --- 1. Build the web page ------------------------------------------------------------------
FROM node:24-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# --- 2. Runtime image -----------------------------------------------------------------------
# The unprivileged variant runs nginx as a non-root user, listening on 8080.
FROM nginxinc/nginx-unprivileged:stable-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/"]
