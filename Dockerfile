# Two stages: build the UI with Node, serve it and the API from one Python process on 8080.
#
# A Dockerfile rather than build autodetection, for two reasons: the repo holds a Node app and a
# Python app that have to ship together, and controlling the npm version here avoids the `npm ci`
# lockfile mismatch that bites when the builder's npm major differs from the one that wrote the lock.

FROM node:22-alpine AS ui
WORKDIR /build
COPY ui/package.json ui/package-lock.json* ./ui/
WORKDIR /build/ui
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi
WORKDIR /build
# The UI imports fixtures directly (ui/src/api.ts, demo-data.ts, alerts-service.ts), so they are part
# of the frontend build input, not just test data. Copy them before building or tsc fails to resolve.
COPY fixtures ./fixtures
COPY ui ./ui
WORKDIR /build/ui
RUN npm run build:demo


FROM python:3.12-slim AS runtime

# curl is here on purpose: the platform runs its healthcheck inside the container, so an image with
# neither curl nor wget fails the check even when the app is perfectly healthy.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

COPY engine/requirements.txt ./engine/requirements.txt
RUN pip install --no-cache-dir -r engine/requirements.txt

COPY engine ./engine
COPY data ./data
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY --from=ui /build/ui/dist ./ui/dist

# Run as a non-root user. Nothing here writes to disk except reports/, which the demo script owns.
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /app/reports \
    && chown -R app:app /app
USER app

EXPOSE 8080

# The platform healthcheck targets 8080, so nothing here may hardcode another port.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/health || exit 1

WORKDIR /app/engine
CMD ["sh", "-c", "exec python -m uvicorn engine.site:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
