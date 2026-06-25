FROM python:3.12-slim

# Use domestic mirrors for faster builds in China
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies with domestic apt mirror
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# ---- dependency layer (cached unless pyproject.toml changes) ----
COPY pyproject.toml ./
# Minimal stub so pip install -e . works before source is copied
RUN mkdir -p src/optagent && touch src/optagent/__init__.py
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -e .

# ---- source layer (rebuilt on any code change, but pip is cached) ----
# Copy all source files
COPY . .

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -e . --no-deps && \
    mkdir -p data/chroma data/checkpoints

EXPOSE 8020
CMD ["uvicorn", "optagent.main:app", "--host", "0.0.0.0", "--port", "8020"]
