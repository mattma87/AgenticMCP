# Multi-stage Dockerfile for AgenticMCP PostgreSQL server
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir -e .

# Final stage
FROM python:3.12-slim

# Set labels
LABEL maintainer="your.email@example.com"
LABEL description="AgenticMCP PostgreSQL server"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 agenticmcp

# Set working directory
WORKDIR /app

# Copy installed package from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy configuration
COPY config/ ./config/

# Create directory for permissions file (can be mounted)
RUN mkdir -p /app/config && \
    chown -R agenticmcp:agenticmcp /app

# Switch to non-root user
USER agenticmcp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_PERMISSIONS_FILE=/app/config/permissions.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the server
ENTRYPOINT ["agenticmcp"]
