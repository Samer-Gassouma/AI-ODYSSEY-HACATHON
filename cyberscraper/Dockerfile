FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    tor \
    chromium \
    chromium-driver \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies in two steps to handle complex dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir numpy scipy pandas && \
    pip install --no-cache-dir -r requirements.txt

# Create cache directories
RUN mkdir -p /app/model_cache /app/sentence_transformers_cache \
    && chmod 777 /app/model_cache \
    && chmod 777 /app/sentence_transformers_cache

# Set environment variables
ENV TRANSFORMERS_CACHE=/app/model_cache
ENV HF_HOME=/app/model_cache
ENV PYTHONUNBUFFERED=1
ENV SENTENCE_TRANSFORMERS_HOME=/app/sentence_transformers_cache

# Copy application code
COPY . .

# Set up entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["docker-entrypoint.sh"]
