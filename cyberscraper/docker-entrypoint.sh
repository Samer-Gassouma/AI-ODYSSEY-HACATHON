#!/bin/bash
set -e

# Create cache directories with proper permissions
mkdir -p /app/model_cache
mkdir -p /app/sentence_transformers_cache
chmod 777 /app/model_cache
chmod 777 /app/sentence_transformers_cache

# Download spaCy model
python -m spacy download en_core_web_sm

# Start Tor service
service tor start

# Start the application
exec python /app/api.py
