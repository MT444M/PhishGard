# Dockerfile final, version robuste

# --- Étape 1: Build ---
FROM ubuntu:22.04 AS builder

# Étape de fiabilisation : Installation des certificats et nettoyage forcé
# Ceci est pour contrer les problèmes de réseau dans l'environnement de build
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Installation des dépendances et de Python
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    gnupg \
    curl && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3.11-venv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN python3.11 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Étape 2: Production ---
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Étape de fiabilisation identique pour l'image de production
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Installation de Python sur l'image de production
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    gnupg && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends \
    python3.11 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY backend/ .
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
ENV NVIDIA_VISIBLE_DEVICES=all
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main_api:app"]