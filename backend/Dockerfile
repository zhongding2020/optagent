FROM python:3.12-slim

# Prevents Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies for chromadb and document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Install Python dependencies (cached as long as pyproject.toml doesn't change)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source code and configuration
COPY src/ src/
COPY config.yaml .
COPY workflows/ workflows/
COPY skills/ skills/

# Create persistent data directories
RUN mkdir -p data/chroma data/checkpoints

EXPOSE 8000

CMD ["uvicorn", "optagent.main:app", "--host", "0.0.0.0", "--port", "8000"]
