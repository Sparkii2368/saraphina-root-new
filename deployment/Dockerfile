# Saraphina Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY saraphina/ ./saraphina/
COPY *.py ./

# Create non-root user
RUN useradd -m -u 1000 saraphina && \
    chown -R saraphina:saraphina /app
USER saraphina

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "web_dashboard:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
