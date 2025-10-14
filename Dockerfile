FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TERM=xterm-256color

# Create app directory
WORKDIR /app

# Install system dependencies (if needed for some Python packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create directories for config and data (will be mounted as volumes)
RUN mkdir -p /app/config /app/data

# Set the entrypoint to run the app
ENTRYPOINT ["python", "-m", "src.app"]
