# Dockerfile mis à jour pour GPU

# --- Étape 1: Build ---
FROM ubuntu:22.04 AS builder

# Install system dependencies with retry and better error handling
RUN for i in {1..3}; do \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3.11-venv \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    break; \
  done || (echo "Failed to install system dependencies after 3 attempts" && exit 1)

WORKDIR /app
COPY backend/requirements.txt .

# Utilise python3.11 explicitement
RUN python3.11 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Étape 2: Production ---
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Install Python 3.11 (required for execution) with retry logic
RUN for i in {1..3}; do \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 && \
    rm -rf /var/lib/apt/lists/* && \
    break; \
  done || (echo "Failed to install python3.11 after 3 attempts" && exit 1)

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY backend/ .
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# On ajoute la variable d'environnement pour que PyTorch voie le GPU
ENV NVIDIA_VISIBLE_DEVICES=all
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main_api:app"]