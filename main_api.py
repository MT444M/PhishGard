# backend/main_api.py

import uvicorn
import datetime
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from googleapiclient.discovery import Resource

# =============================================================================
# CONFIGURATION DU LOGGING
# =============================================================================
from config.logging_config import setup_logging, get_logger

# Initialiser le logging au démarrage
setup_logging()
logger = get_logger(__name__)

# =============================================================================
# IMPORTS DES MODULES PERSONNALISÉS
# =============================================================================
from dashboard import dashboard_service
from dashboard.schemas import DashboardResponse

from core.email_orchestrator import EmailOrchestrator
from core.url_orchestrator import URLOrchestrator
from core.header_orchestrator import HeaderOrchestrator
from core import email_client

from database import models
from database.database import engine, get_db

from auth import auth_router, auth_service

# =============================================================================
# CRÉATION DES TABLES DE LA BASE DE DONNÉES
# =============================================================================
# Cette ligne crée les tables définies dans `models.py` si elles n'existent pas
# Tenter de se connecter à la base de données avec gestion des erreurs robuste
try:
    # Essayer de se connecter à la base de données et de créer les tables
    from database.database import DB_HOST, DB_PORT, DB_NAME, DB_USER
    logger.info(f"Tentative de connexion à la base de données PostgreSQL sur {DB_HOST}:{DB_PORT}/{DB_NAME} avec l'utilisateur {DB_USER}")
    
    # Vérifier que la connexion fonctionne en essayant une simple requête
    # Cette partie peut échouer si la base de données n'est pas accessible
    try:
        with engine.connect() as conn:
            # Utiliser une syntaxe compatible avec toutes les versions de SQLAlchemy
            conn.exec_driver_sql("SELECT 1")
            logger.info("Connexion à la base de données PostgreSQL établie avec succès")
            
        # Une fois la connexion confirmée, créer les tables
        models.Base.metadata.create_all(bind=engine)
        logger.info("Tables de base de données créées/vérifiées")
    except Exception as e:
        logger.error(f"Erreur lors de l'accès à la base de données: {e}")
        logger.warning("L'application va démarrer, mais les fonctionnalités liées à la base de données ne seront pas disponibles")
        
# Capturer toutes les autres erreurs potentielles liées à la configuration de la BDD
except Exception as e:
    logger.error(f"ERREUR CRITIQUE - Problème avec la configuration de la base de données: {e}")
    logger.warning("L'application va démarrer avec des fonctionnalités limitées")

# =============================================================================
# INITIALISATION DE L'APPLICATION FastAPI
# =============================================================================
app = FastAPI(
    title="PhishGard-AI API",
    description="API pour l'analyse d'emails et d'URLs afin de détecter le phishing.",
    version="1.0.0"
)

logger.info("Application FastAPI initialisée")

# Configuration CORS (Cross-Origin Resource Sharing)
# INDISPENSABLE pour que le frontend puisse communiquer avec le backend
app.add_middleware(
    CORSMiddleware,
    # Pour la production, spécifiez les domaines exacts au lieu de "*"
    # "*" et allow_credentials=True sont incompatibles selon les navigateurs
    # Temporairement accepter toutes les origines pour faciliter le débogage
    # Une fois que l'application fonctionne correctement, remplacer "*" par les URLs spécifiques
    allow_origins=["*"],
    # IMPORTANT: allow_credentials=False est obligatoire quand allow_origins=["*"]
    # sinon les navigateurs bloquent les requêtes CORS
    allow_credentials=False,
    # Voici les URLs spécifiques si vous souhaitez les réactiver plus tard avec allow_credentials=True:
    # allow_origins=[
    #    "http://127.0.0.1:8000",
    #    "http://localhost:8000", 
    #    "https://phishgard.usts.ai",
    #    "https://hk8484gs8wgso4scw0ckcc8s",
    #    "http://hk8484gs8wgso4scw0ckcc8s",  # Version non-HTTPS 
    #    "https://phishgard.coolify.io"
    # ],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Middleware CORS configuré")

# Inclusion du routeur d'authentification
app.include_router(auth_router.router)
logger.info("Routeur d'authentification inclus")

# =============================================================================
# MODÈLES DE DONNÉES (Pydantic)
# =============================================================================
# Pydantic assure que les données envoyées à l'API ont le bon format

class URLAnalyzeRequest(BaseModel):
    """Modèle pour les requêtes d'analyse d'URL"""
    url: str = Field(..., example="http://example-phishing-site.com")

class EmailAnalyzeRequest(BaseModel):
    """Modèle pour les requêtes d'analyse d'email"""
    # Pour l'instant on se base sur l'ID, on pourra ajouter le contenu brut plus tard
    email_id: str = Field(..., example="197640cc612987c5")

class HeaderAnalyzeRequest(BaseModel):
    """Modèle pour les requêtes d'analyse d'en-tête brut"""
    raw_header: str = Field(
        ..., 
        example="Received: from mail-sor-f69.google.com (mail-sor-f69.google.com. [209.85.220.69]) by mx.google.com ..."
    )

class UserResponse(BaseModel):
    """Modèle de réponse pour les informations utilisateur"""
    # Bonne pratique pour ne pas renvoyer de données sensibles comme les tokens
    email: str
    google_id: str

    class Config:
        from_attributes = True  # Version Pydantic V2 (remplacement de orm_mode)

# =============================================================================
# ENDPOINTS GÉNÉRAUX
# =============================================================================

@app.get("/api")
def read_root():
    """Endpoint racine pour vérifier que l'API est en ligne"""
    logger.info("Endpoint racine appelé")
    return {"status": "PhishGard-AI API est en ligne"}

@app.get("/health")
def health_check():
    """Endpoint de diagnostic pour vérifier l'état des services"""
    logger.info("Healthcheck endpoint appelé")
    
    # Vérifier l'état de la base de données
    db_status = "OK"
    db_error = None
    
    try:
        # Utiliser with engine.connect() pour éviter les problèmes de contexte
        with engine.connect() as conn:
            # Simple requête pour vérifier que la connexion fonctionne
            conn.execute("SELECT 1")
    except Exception as e:
        db_status = "ERROR"
        db_error = str(e)
    
    return {
        "service": "PhishGard API",
        "status": "UP",
        "timestamp": datetime.datetime.now().isoformat(),
        "database": {
            "status": db_status,
            "error": db_error,
            "host": os.getenv("DB_HOST", "not set"),
            "database": os.getenv("DB_NAME", "not set")
        },
        "environment": os.getenv("ENV", "development")
    }

# =============================================================================
# ENDPOINTS GESTION UTILISATEUR
# =============================================================================

@app.get("/api/users/me", response_model=UserResponse)
def get_logged_in_user(current_user: models.User = Depends(auth_service.get_current_user)):
    """
    Endpoint protégé qui renvoie les informations de l'utilisateur actuellement connecté.
    La dépendance `get_current_user` gère toute la validation du cookie JWT.
    """
    logger.info(f"Récupération des informations utilisateur pour ID: {current_user.id}")
    return current_user

# =============================================================================
# ENDPOINTS GESTION DES EMAILS
# =============================================================================

@app.get("/api/emails")
def get_email_list(
    current_user: models.User = Depends(auth_service.get_current_user),
    gmail_service: Resource = Depends(auth_service.get_gmail_service)
):
    """
    Endpoint SÉCURISÉ pour récupérer la liste des emails pour l'utilisateur connecté.
    """
    logger.info(f"Récupération de la liste des emails pour l'utilisateur {current_user.email}")
    
    if not gmail_service:
        logger.error("Service Gmail non disponible")
        raise HTTPException(status_code=503, detail="Service Gmail non disponible.")
    
    try:
        # Récupère les 10 derniers emails de la boîte de réception
        live_emails = email_client.get_emails(gmail_service, max_results=10)
        logger.info(f"Récupération de {len(live_emails)} emails depuis Gmail")
        
        # Formatte les données pour le frontend
        # Notez qu'il n'y a PAS de verdict ou de score ici au début
        formatted_emails = []
        for email in live_emails:
            formatted_emails.append({
                "id": email.get('id'),
                "sender": email.get('sender'),
                "subject": email.get('subject'),
                "preview": email.get('snippet', ''),  # Le snippet de l'API Gmail est parfait pour l'aperçu
                "body": email.get('body', ''),  # Le corps de l'email
                "html_body": email.get('html_body', ''),  # Le corps HTML de l'email
                "timestamp": email.get('timestamp', ''),  # Le timestamp de l'email
            })
        
        logger.info(f"Emails formatés avec succès: {len(formatted_emails)} emails")
        return formatted_emails
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des emails live: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Une erreur est survenue lors de la récupération des emails: {e}"
        )

@app.post("/api/analyze/email")
def analyze_email(
    request: EmailAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user),
    gmail_service: Resource = Depends(auth_service.get_gmail_service)
):
    """
    Analyse un email complet en utilisant son ID.
    Vérifie le cache en BDD et sauvegarde le nouveau résultat.
    Applique les libellés appropriés sur Gmail.
    """
    logger.info(f"Demande d'analyse d'email ID: {request.email_id} pour l'utilisateur {current_user.email}")
    
    if not gmail_service:
        logger.error("Service Gmail non disponible pour l'analyse d'email")
        raise HTTPException(status_code=503, detail="Service Gmail non disponible.")
    
    try:
        email_data_list = email_client.get_emails(gmail_service, email_id=request.email_id)
        if not email_data_list:
            logger.warning(f"Email avec l'ID {request.email_id} non trouvé")
            raise HTTPException(
                status_code=404, 
                detail=f"Email avec l'ID {request.email_id} non trouvé."
            )
        
        email_data = email_data_list[0]
        logger.info(f"Email récupéré avec succès: {email_data.get('subject', 'Sans sujet')}")
        
        # On l'instancie ici, en lui passant la session de BDD de la requête
        email_orchestrator = EmailOrchestrator(db=db)

        # On passe maintenant l'ID de l'utilisateur à l'orchestrateur
        final_report = email_orchestrator.run_full_analysis(
            email_data, 
            gmail_service=gmail_service, 
            user_id=current_user.id
        )

        logger.info(f"Analyse d'email terminée avec succès pour ID: {request.email_id}")
        return final_report
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'email {request.email_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Une erreur interne est survenue: {e}"
        )

# =============================================================================
# ENDPOINTS ANALYSE D'EN-TÊTES
# =============================================================================

@app.post("/api/analyze/header")
def analyze_raw_header(request: HeaderAnalyzeRequest):
    """
    Analyse un en-tête d'e-mail brut fourni dans le corps de la requête.
    """
    logger.info("Demande d'analyse d'en-tête brut reçue")
    
    try:
        # On instancie notre nouvel orchestrateur
        header_orchestrator = HeaderOrchestrator()
        final_report = header_orchestrator.run_header_analysis(request.raw_header)
        
        logger.info("Analyse d'en-tête brut terminée avec succès")
        return final_report
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du header brut: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Une erreur interne est survenue: {str(e)}"
        )

# =============================================================================
# ENDPOINTS ANALYSE D'URLs
# =============================================================================

@app.post("/api/url/context")
def get_url_contextual_analysis(request: URLAnalyzeRequest):
    """
    Endpoint pour l'analyse 'humaine'.
    Récupère des informations contextuelles détaillées sur une URL (WHOIS, DNS, SSL...).
    """
    logger.info(f"Demande d'analyse contextuelle pour l'URL: {request.url}")
    
    try:
        orchestrator = URLOrchestrator(request.url)
        analysis_result = orchestrator.run_contextual_analysis()
        
        logger.info(f"Analyse contextuelle terminée avec succès pour: {request.url}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse contextuelle de l'URL {request.url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Une erreur interne est survenue: {str(e)}"
        )

@app.post("/api/url/predict")
def get_url_prediction(request: URLAnalyzeRequest):
    """
    Endpoint pour la prédiction 'machine'.
    Analyse une URL et renvoie le verdict du modèle de Machine Learning.
    """
    logger.info(f"Demande de prédiction pour l'URL: {request.url}")
    
    try:
        orchestrator = URLOrchestrator(request.url)
        prediction_result = orchestrator.run_prediction()
        
        logger.info(f"Prédiction terminée avec succès pour: {request.url}")
        return prediction_result
        
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction pour l'URL {request.url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Une erreur interne est survenue: {str(e)}"
        )

# =============================================================================
# ENDPOINTS TABLEAU DE BORD
# =============================================================================

@app.get("/api/dashboard/summary", response_model=DashboardResponse)
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user),
    period: str = "7d",  # On garde une valeur par défaut
    start_date: Optional[str] = None,  # Date de début personnalisée
    end_date: Optional[str] = None  # Date de fin personnalisée
):
    """
    Endpoint principal pour le dashboard.
    Accepte une période prédéfinie ('today', '7d', '30d') ou une plage de dates personnalisée.
    """
    logger.info(f"Génération du dashboard pour l'utilisateur {current_user.email} - Période: {period}")
    
    try:
        # On passe tous les paramètres au service, qui contiendra la logique
        summary_data = dashboard_service.get_dashboard_summary(
            db=db,
            user_id=current_user.id,
            period=period,
            custom_start_date=start_date,
            custom_end_date=end_date
        )
        
        logger.info(f"Dashboard généré avec succès pour l'utilisateur {current_user.email}")
        return summary_data
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du résumé du dashboard pour l'utilisateur {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

# =============================================================================
# MONTAGE DU DOSSIER STATIC
# =============================================================================
# Cette ligne est la plus importante: elle "monte" le dossier `static`
# pour qu'il soit servi par FastAPI.
# html=True indique de servir index.html pour les requêtes à la racine.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
logger.info("Dossier static monté avec succès")

# =============================================================================
# DÉMARRAGE DU SERVEUR
# =============================================================================
if __name__ == "__main__":
    logger.info("Démarrage du serveur PhishGard-AI sur http://127.0.0.1:8000")
    # Pour un rechargement automatique lors des modifications de code
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)