# syntax=docker/dockerfile:1.4
# ==============================================================================
# Production Dockerfile for Zomato AI Restaurant Recommendation Service
# Multi-stage, non-root, security-hardened container image
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build & Dependencies
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt .

# Install dependencies into /install prefix
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Runtime Container
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runner

LABEL maintainer="AI Restaurant Concierge Team"
LABEL description="AI-powered Zomato restaurant recommendation engine with Groq LPU inference"
LABEL version="1.0.0"

WORKDIR /app

# Install minimal runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder prefix
COPY --from=builder /install /usr/local

# Create non-root system user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy application source tree
COPY src/ /app/src/
COPY frontend/ /app/frontend/
COPY ui/ /app/ui/
COPY data/ /app/data/
COPY entrypoint.sh /app/entrypoint.sh

# Ensure proper permissions and strip carriage returns for non-root user
RUN sed -i 's/\r$//' /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=INFO

# Expose service port
EXPOSE 8000

# Container Healthcheck (polls /health endpoint every 30s)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/health || exit 1

# Launch service via entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
