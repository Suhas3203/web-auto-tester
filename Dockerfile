# ── Stage 1: Install dependencies ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

# ── Stage 2: Final minimal image (no Chromium — lite mode uses httpx only) ───
FROM python:3.12-slim

# Minimal system deps for lxml (BeautifulSoup) — no Chromium needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pre-built Python deps
COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages/

# Copy application code (only what's needed)
COPY web_auto_tester/ ./web_auto_tester/
COPY app.py .
COPY run_tests.py .
COPY pyproject.toml .

# Create reports dir
RUN mkdir -p /tmp/web-auto-tester-reports

# ── Environment ──────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REPORTS_DIR=/tmp/web-auto-tester-reports \
    RENDER=true \
    MALLOC_ARENA_MAX=2

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:10000/health')" || exit 1

# Single uvicorn worker, long timeout for crawling
CMD ["python", "-m", "uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "10000", \
     "--workers", "1", \
     "--timeout-keep-alive", "120"]
