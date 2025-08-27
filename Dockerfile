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

# Expédier le port pour l'application
EXPOSE 8000

# Port configurable via variable d'environnement
ENV PORT=8000 \
    # Variables d'environnement pour la base de données Coolify
    DB_HOST="hk8484gs8wgso4scw0ckcc8s" \
    DB_PORT="5432" \
    DB_USER="postgres" \
    DB_PASSWORD="DGkv6CnuAcaIl6SfdQhfo4x3rxikvcZLBYQT53Ix6p1hBZufjfm3RTwmTuhKwRGx" \
    DB_NAME="postgres" \
    # Configuration du domaine et de l'environnement
    ENV="production" \
    HOST="phishgard.paulette.usts.ai" \
    # Si aucune URL fournie, elles seront construites à partir de HOST
    # FRONTEND_URL="https://phishgard.paulette.usts.ai/" \
    # GOOGLE_REDIRECT_URI="https://phishgard.paulette.usts.ai/api/auth/callback" \
    # S'assurer que secure est true en production pour les cookies
    SECURE_COOKIES="true"

# Commande pour démarrer l'application en production
# Utilise un fichier de configuration explicite pour gunicorn
CMD ["gunicorn", "--config", "gunicorn_config.py", "main_api:app"]