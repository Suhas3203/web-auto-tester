# ── Stage 1: Install dependencies ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

# ── Stage 2: Final minimal image ─────────────────────────────────────────────
FROM python:3.12-slim

# System deps for Chromium (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libx11-xcb1 libxcomposite1 \
    libxdamage1 libxrandr2 libxshmfence1 \
    libpango-1.0-0 libcairo2 xdg-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy pre-built Python deps
COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages/

# Install ONLY Chromium (not Firefox/WebKit — saves ~300MB)
RUN playwright install chromium \
    && playwright install-deps chromium 2>/dev/null || true

# Copy application code (only what's needed)
COPY web_auto_tester/ ./web_auto_tester/
COPY app.py .
COPY run_tests.py .
COPY pyproject.toml .

# Create reports dir with proper permissions
RUN mkdir -p /tmp/web-auto-tester-reports

# ── Memory-optimized environment ─────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REPORTS_DIR=/tmp/web-auto-tester-reports \
    RENDER=true \
    # Limit Python's own memory usage
    MALLOC_ARENA_MAX=2 \
    # Tell Chromium to use /tmp for shared memory (Docker /dev/shm is only 64MB)
    CHROMIUM_FLAGS="--disable-dev-shm-usage"

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:10000/health || exit 1

# Single uvicorn worker to minimize memory, increase timeout for long test runs
CMD ["python", "-m", "uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "10000", \
     "--workers", "1", \
     "--timeout-keep-alive", "120"]
