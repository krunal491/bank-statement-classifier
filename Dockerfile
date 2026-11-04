FROM python:3.11-slim

# Tesseract (OCR) + the shared libs opencv-python-headless needs at import time.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY src/ src/
COPY data/ data/
# Build with the deployed sklearn version so the first upload never has to train.
RUN python -c "from src.classifier.ml_model import train; train()"
RUN python -m backend.ml_eval
# Each OCR worker uses one CPU thread; avoid nested Tesseract thread contention.
ENV OMP_THREAD_LIMIT=1
# samples/ is intentionally not copied: it's only used by the tests, cli.py and the
# dataset scripts, never by the deployed API.

EXPOSE 8000
HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8000}/api/health || exit 1

# Render (and Railway) inject $PORT at runtime; fall back to 8000 for local `docker run`.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
