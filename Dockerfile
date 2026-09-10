# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_DEBUG=false

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Ensure upload directories exist
RUN mkdir -p uploads/avatars uploads/documents instance

EXPOSE 5000

# Start with Gunicorn production server with dynamic PORT fallback
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 4 --timeout 120"]

