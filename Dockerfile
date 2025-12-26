# Use Python 3.10-slim (stable, compatible with all packages)
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies (needed for google-cloud-storage, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with specific versions for reproducibility
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create directory for temp uploads
RUN mkdir -p temp_uploads

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run with gunicorn (production-ready)
# Workers=1 for simplicity (can increase if needed)
# Threads=8 for concurrency within the worker
# Timeout=0 for long-running Veo operations
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "--access-logfile", "-", "--error-logfile", "-", "web_app:app"]

