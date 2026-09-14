# Multi-stage build: a `builder` stage resolves dependencies with uv into
# a self-contained virtualenv, then the runtime stage copies only that
# venv plus the application source -- no compiler toolchain, no uv
# itself, no build cache ships in the final image.

FROM python:3.11-slim AS builder

# libpq/mysqlclient-style C extensions aren't needed (aiomysql/pymysql
# are pure Python), but cryptography and Pillow both build/link native
# code, so the builder stage keeps a compiler around; the runtime stage
# below does not.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

# Dependencies first, so an app-code-only change doesn't invalidate this
# (expensive) layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

FROM python:3.11-slim AS runtime

RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app

EXPOSE 8000

# /ready round-trips the database -- a real readiness check, not just
# "the process is alive". See app/main.py.
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/ready', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
