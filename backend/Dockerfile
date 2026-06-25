FROM python:3.12-slim

# Use domestic mirrors for faster builds in China
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# System dependencies with domestic apt mirror
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source code and configuration
COPY src/ src/
COPY config.yaml .
COPY workflows/ workflows/
COPY skills/ skills/

RUN mkdir -p data/chroma data/checkpoints

EXPOSE 8020

CMD ["uvicorn", "optagent.main:app", "--host", "0.0.0.0", "--port", "8020"]
