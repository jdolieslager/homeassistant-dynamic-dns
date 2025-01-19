# Build stage
FROM python:3.12-slim AS builder

# Create non-root user first
RUN useradd -m -r runner

# Create and set working directory
WORKDIR /app
RUN chown runner:runner /app

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER runner

# Set environment variables
ENV PATH=/home/runner/.local/bin:$PATH

# Install Python dependencies
COPY --chown=runner:runner requirements_test.txt .
RUN pip install --no-cache-dir --user -r requirements_test.txt

# Final stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH=/home/runner/.local/bin:$PATH

# Create non-root user first
RUN useradd -m -r runner

# Create and set working directory
WORKDIR /app
RUN chown runner:runner /app

# Copy Python packages and binaries from builder
COPY --from=builder /home/runner/.local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder --chown=runner:runner /home/runner/.local/bin /home/runner/.local/bin

# Switch to non-root user
USER runner

# Run tests by default
CMD ["pytest", "--cov=custom_components.dynamic_dns", "-v", "--cov-report=term-missing"] 