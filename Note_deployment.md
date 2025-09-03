# Docker Architecture Overview

###  🐳 Built Images

  - phishgard-app:latest (22.4GB) - Main application image
    - Based on nvcr.io/nvidia/pytorch:23.10-py3 (NVIDIA container with CUDA support)
    - Contains Python 3.10, PyTorch 2.1.0a0, and all application dependencies
    - Multi-stage build for security (non-root appuser)
  - postgres:15-alpine (274MB) - Database image
    - Lightweight Alpine Linux PostgreSQL 15
    - Data persisted via Docker volume

###  🔗 Database Connection

  Environment Variables (from .env → container):
  POSTGRES_USER=phishgard_user
  POSTGRES_PASSWORD=phishgard_db_PASSWORD
  POSTGRES_DB=phishgard_db
  DATABASE_URL=postgresql://phishgard_user:phishgard_db_PASSWORD@db:5432/phishgard_db

  Connection Flow:
  1. App container connects to db container using Docker internal network
  2. SQLAlchemy ORM manages database operations
  3. Alembic (not shown) would handle migrations
  4. Database schema auto-created on startup via models.Base.metadata.create_all()

###  🏗️ Build Process

  Dockerfile (NVIDIA GPU-enabled):
  FROM nvcr.io/nvidia/pytorch:23.10-py3  # Base image with CUDA
  WORKDIR /app
  COPY backend/requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY backend/ .
  RUN useradd --create-home appuser
  USER appuser
  EXPOSE 8000
  CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main_api:app"]

  docker-compose.yml orchestrates:
  - App service (port 8000:8000) with GPU access
  - DB service (port 5432) with volume persistence
  - Environment variables injected from .env
  - Dependency ordering (app depends_on db)

###  🌐 Network Architecture

  ┌─────────────────┐    ┌─────────────────┐
  │   Frontend      │    │   Backend App   │
  │   (Static)      │◄──►│   (FastAPI)     │
  │   localhost:8000│    │   localhost:8000│
  └─────────────────┘    └─────────┬───────┘
                                   │
                                   ▼
                           ┌─────────────────┐
                           │   PostgreSQL    │
                           │   db:5432       │
                           └─────────────────┘

###  🔐 Authentication Flow

  1. User clicks login → /api/auth/login
  2. Redirect to Google OAuth consent screen
  3. Google callback → /api/auth/callback?code=...
  4. Token exchange → JWT creation → HttpOnly cookie
  5. Cookie domain dynamically set based on CALLBACK_DOMAIN

###  📊 Current Status

  ✅ App running: http://localhost:8000✅ Database connected: PostgreSQL on internal network✅ Authentication working: OAuth2 with Google✅ Email analysis: Gmail integration functional✅
  Dashboard operational: Statistics and reporting

  **The architecture successfully handles both local development and production deployment through environment-based configuration.**