# Use Python 3.11 slim image for optimal performance and size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for optimization
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies (minimal for lightweight operation)
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip==23.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create directories for input/output
RUN mkdir -p /app/input /app/output /app/logs

# Set memory limits for optimal performance
ENV PYTHONMALLOC=malloc

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import app; print('Health OK')" || exit 1

# Default command
CMD ["python", "app.py"]