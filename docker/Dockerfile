# CCBM Production Docker Image
FROM python:3.11-slim

# Metadata
LABEL maintainer="sergeeey"
LABEL version="1.0.0"
LABEL description="Certified Context Budget Manager - Production"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY pyproject.toml .

# Install CCBM
RUN pip install -e .

# Expose ports
EXPOSE 8000  # API
EXPOSE 8501  # Dashboard

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import ccbm; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "ccbm.mcp.server"]
