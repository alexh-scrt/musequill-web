# MuseQuill Newsletter Service Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY newsletter_requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY newsletter_service.py .
COPY .env.example .env

# Create directories
RUN mkdir -p /app/data /app/logs /app/backups

# Create non-root user
RUN useradd --create-home --shell /bin/bash newsletter
RUN chown -R newsletter:newsletter /app
USER newsletter

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DATABASE_PATH=/app/data/newsletter.db
ENV HOST=0.0.0.0
ENV PORT=8080

# Run the application
CMD ["python", "newsletter_service.py"]
