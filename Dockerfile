FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Development stage
FROM base as development
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy source code (will be overridden by volume in dev)
COPY . .

# Create directories
RUN mkdir -p /app/logs

# Development server with reload
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
RUN pip install --no-cache-dir -r requirements.txt

# Copy only source code
COPY src/ ./src/
COPY database/ ./database/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]