# Dockerfile

# --- Étape 1: Build ---
# Utilise une image Python complète pour installer les dépendances
FROM python:3.11-slim as builder

# Définit le répertoire de travail
WORKDIR /app

# Copie le fichier des dépendances
COPY requirements.txt .

# Installe les dépendances dans un environnement virtuel
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Étape 2: Production ---
# Utilise une image plus légère pour l'exécution
FROM python:3.11-slim

# Définit le répertoire de travail
WORKDIR /app

# Copie l'environnement virtuel de l'étape de build
COPY --from=builder /opt/venv /opt/venv

# Copie le code de l'application
COPY . .

# Active l'environnement virtuel
ENV PATH="/opt/venv/bin:$PATH"

# Crée un utilisateur non-root pour des raisons de sécurité
RUN useradd --create-home appuser
USER appuser

# Commande pour démarrer l'application en production
# Coolify peut surcharger le port, mais c'est bien de l'exposer
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main_api:app"]