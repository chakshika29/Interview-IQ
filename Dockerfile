# Official lightweight Python 3.12 slim image
FROM python:3.12-slim

# Ensure stdout/stderr are flushed immediately
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install curl for healthcheck probe
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and assets
COPY app/ app/
COPY samples/ samples/
COPY data/ data/
COPY streamlit_app.py .

# Create persistent storage directories
RUN mkdir -p storage/sessions storage/recordings .cache

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default: Start FastAPI REST Backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
