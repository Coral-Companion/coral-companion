FROM pytorch/pytorch:2.14.0-cuda13.2-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN which python && \
    apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv 
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Use a cache so local builds don't download all requirements if already present
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY app ./app
COPY third_party ./third_party

# Set default configuration environment variables
ENV EMBEDDING_VECTOR_DISTANCE_THRESHOLD=0.2
ENV CROPPING_PADDING_RATIO=0.1
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]