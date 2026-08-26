# syntax=docker/dockerfile:1

# Stage 1: Build frontend assets (Tailwind CSS)
FROM node:18-alpine AS assets
WORKDIR /build
# Copy only files needed to build Tailwind first (leverage cache)
COPY package.json tailwind.config.js ./
COPY app/static/css/tailwind.input.css ./app/static/css/tailwind.input.css
# Tailwind needs to scan templates for class usage
COPY app/templates ./app/templates
COPY app ./app
RUN npm install --no-audit --no-fund \
  && npx tailwindcss -c tailwind.config.js \
       -i app/static/css/tailwind.input.css \
       -o app/static/css/tailwind.css \
       --minify

# Base image
FROM python:3.12-slim AS base

# Prevents Python from writing .pyc files and buffers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies (psycopg2, Pillow, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
       libjpeg62-turbo-dev \
       zlib1g-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirement spec first to leverage Docker layer caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip check || true

# Copy project files
COPY . .

# Copy built Tailwind CSS from assets stage
COPY --from=assets /build/app/static/css/tailwind.css /app/app/static/css/tailwind.css

# Environment defaults (override in runtime)
ENV FLASK_ENV=production \
    PYTHONPATH=/app

# Expose the app port
EXPOSE 8000

# Create a non-root user for security
RUN useradd -m appuser \
    && chown -R appuser:appuser /app
USER appuser

# Run with Gunicorn using the WSGI entrypoint
# Adjust workers/threads based on your server resources
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "2", "--threads", "4", "--timeout", "60", "wsgi:app"]
