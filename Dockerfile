# WHY: Use official lightweight Python 3.12 slim image to minimize container footprint
FROM python:3.12-slim

# WHY: Ensure stdout/stderr are flushed immediately and prevent writing unnecessary .pyc bytecode
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory inside the container
WORKDIR /app

# WHY: Install curl for container healthcheck support
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# WHY: Copy requirements first to leverage Docker layer caching during rebuilds
COPY requirements.txt .

# WHY: Install only production dependencies without caching wheels
RUN pip install --no-cache-dir -r requirements.txt

# WHY: Copy application source code and sample data (excluding secrets via .dockerignore)
COPY app/ app/
COPY samples/ samples/
COPY streamlit_app.py .

# WHY: Expose ports for both the FastAPI REST backend (8000) and the Streamlit UI (8501)
EXPOSE 8000 8501

# WHY: Healthcheck probe checks /health endpoint every 30 seconds
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Launch FastAPI server with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
