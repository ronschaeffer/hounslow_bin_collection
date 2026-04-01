# Stage 1: Builder — install Poetry, export requirements, build wheel
FROM python:3.11-slim AS builder

WORKDIR /build

# Install Poetry and export plugin
RUN pip install --no-cache-dir poetry poetry-plugin-export

# Copy dependency files first (cache-friendly layer)
COPY pyproject.toml poetry.lock ./

# Export requirements (no dev deps)
RUN poetry export --without dev -f requirements.txt -o requirements.txt

# Copy source and build the wheel
COPY src/ src/
COPY README.md ./
RUN poetry build -f wheel


# Stage 2: Runtime — lean image with Playwright and production deps
FROM python:3.11-slim

WORKDIR /app

# Install Playwright system dependencies + cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    libnspr4 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libcairo2 \
    libpango-1.0-0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies from exported requirements
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Install the built wheel
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Install Playwright Chromium browser
RUN playwright install chromium

# Copy config defaults
COPY config/config.yaml.example /app/config-defaults/config.yaml.example

# Create directories
RUN mkdir -p /app/config /app/output

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["hounslow-bins", "all"]
