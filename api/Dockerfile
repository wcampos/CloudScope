FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    make \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/static /app/uploads /app/tests/data /app/migrations

# Copy application code
COPY api/ .

# Create non-root user and set permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/data /app/logs /app/static /app/uploads /app/tests/data /app/migrations && \
    chmod -R 755 /app

ENV PYTHONPATH=/app

USER appuser

# Expose port
EXPOSE 5000

# Run the API service
CMD ["python", "app.py"] 