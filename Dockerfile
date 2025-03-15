FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    make \
    curl \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create volume directories
RUN mkdir -p /app/data /app/logs /app/static /app/uploads /app/tests/data

# Copy application code
COPY . .

# Create non-root user and set permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/data /app/logs /app/static /app/uploads /app/tests/data

USER appuser

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"] 