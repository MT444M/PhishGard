# Dockerfile mis à jour pour GPU

# --- Étape 1: Build ---
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 AS builder

# Installe les dépendances système comme Python et pip
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .

# Utilise python3.11 explicitement
RUN python3.11 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Étape 2: Production ---
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Installe python3.11 (nécessaire pour l'exécution)
RUN apt-get update && apt-get install -y \
    python3.11 \
    && rm -rf /var/lib/apt/lists/*

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