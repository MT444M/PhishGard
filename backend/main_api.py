# backend/main_api.py

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session 
from fastapi.middleware.cors import CORSMiddleware

from dashboard import dashboard_service
from dashboard.schemas import DashboardResponse 

from pydantic import BaseModel, Field
import json
from typing import Optional 
import os

# --- Import de vos modules d'analyse ---
# Nous ajustons les imports pour qu'ils fonctionnent depuis le dossier backend/
from core.email_orchestrator import EmailOrchestrator
from core.url_orchestrator import URLOrchestrator
from core.header_orchestrator import HeaderOrchestrator
from core import email_client # On garde l'authentification

from database import crud, models
from database.database import SessionLocal, engine

# ==============================================================================
# 0. CRÉATION DES TABLES DE LA BASE DE DONNÉES
# ==============================================================================
# Cette ligne crée les tables définies dans `models.py` si elles n'existent pas.
models.Base.metadata.create_all(bind=engine)

# ==============================================================================
# 1. INITIALISATION DE L'APPLICATION FastAPI
# ==============================================================================
app = FastAPI(
    title="PhishGard-AI API",
    description="API pour l'analyse d'emails et d'URLs afin de détecter le phishing.",
    version="1.0.0"
)

# --- Configuration CORS (Cross-Origin Resource Sharing) ---
# C'est INDISPENSABLE pour que votre frontend (qui tournera sur un port différent)
# puisse communiquer avec votre backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, vous devriez restreindre à l'URL de votre frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 2. MODÈLES DE DONNÉES (Pydantic)
# ==============================================================================
# Pydantic assure que les données envoyées à votre API ont le bon format.

class URLAnalyzeRequest(BaseModel):
    url: str = Field(..., example="http://example-phishing-site.com")

class EmailAnalyzeRequest(BaseModel):
    # Pour l'instant on se base sur l'ID, on pourra ajouter le contenu brut plus tard
    email_id: str = Field(..., example="197640cc612987c5")

class HeaderAnalyzeRequest(BaseModel):
    raw_header: str = Field(..., example="Received: from mail-sor-f69.google.com (mail-sor-f69.google.com. [209.85.220.69])\n by mx.google.com ...")




# ==============================================================================
# 3. GESTION DE LA SESSION DE BASE DE DONNÉES
# ==============================================================================
# Dépendance FastAPI pour obtenir une session de BDD par requête
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SUPPRIMER L'INITIALISATION GLOBALE DE L'ORCHESTRATEUR ---
# email_orchestrator = EmailOrchestrator() # <== SUPPRIMER CETTE LIGNE
gmail_service = email_client.authenticate_gmail()



# ==============================================================================
# 4. DÉFINITION DES ENDPOINTS DE L'API
# ==============================================================================
# Endpoint racine pour vérifier que l'API est en ligne
@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API PhishGard-AI. Utilisez /api pour accéder aux fonctionnalités."}

@app.get("/api")
def read_root():
    return {"status": "PhishGard-AI API est en ligne"}



@app.get("/api/emails")
def get_email_list():
    """
    Endpoint pour récupérer la liste des emails depuis le service Gmail.
    """
    if not gmail_service:
        raise HTTPException(status_code=503, detail="Service Gmail non disponible.")
    
    try:
        # Récupère les 25 derniers emails de la boîte de reception
        live_emails = email_client.get_emails(gmail_service, max_results= 10)
        
        # Formatte les données pour le frontend.
        # Notez qu'il n'y a PAS de verdict ou de score ici au début.
        formatted_emails = []
        for email in live_emails:
            formatted_emails.append({
                "id": email.get('id'),
                "sender": email.get('sender'),
                "subject": email.get('subject'),
                "preview": email.get('snippet', ''), # Le snippet de l'API Gmail est parfait pour l'aperçu
                "body": email.get('body', ''),  # Le corps de l'email
                "html_body": email.get('html_body', ''),  # Le corps HTML de l'email
                "timestamp": email.get('timestamp', ''),  # Le timestamp de l'email
            })
            #debug
        return formatted_emails
        
    except Exception as e:
        print(f"Erreur lors de la récupération des emails live: {e}")
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue lors de la récupération des emails: {e}")
    


@app.post("/api/analyze/email") 
def analyze_email(request: EmailAnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyse un email complet en utilisant son ID.
    Vérifie le cache en BDD et sauvegarde le nouveau résultat.
    et applique les libellés appropriés sur Gmail.
    """
    if not gmail_service:
        raise HTTPException(status_code=503, detail="Service Gmail non disponible.")
    
    try:
        email_data_list = email_client.get_emails(gmail_service, email_id=request.email_id)
        if not email_data_list:
            raise HTTPException(status_code=404, detail=f"Email avec l'ID {request.email_id} non trouvé.")
        
        email_data = email_data_list[0]
        
        # --- MODIFIER L'INSTANCIATION DE L'ORCHESTRATEUR ---
        # On l'instancie ici, en lui passant la session de BDD de la requête
        email_orchestrator = EmailOrchestrator(db=db)

        final_report = email_orchestrator.run_full_analysis(email_data, gmail_service=gmail_service)

        return final_report
    except Exception as e:
        print(f"Erreur lors de l'analyse de l'email: {e}")
        raise HTTPException(status_code=500, detail=f"Une erreur interne est survenue: {e}")

    

# --- NOUVEAUX Endpoints pour les URLs ---

@app.post("/api/url/context")
def get_url_contextual_analysis(request: URLAnalyzeRequest):
    """
    Endpoint pour l'analyse 'humaine'.
    Récupère des informations contextuelles détaillées sur une URL (WHOIS, DNS, SSL...).
    """
    try:
        orchestrator = URLOrchestrator(request.url)
        analysis_result = orchestrator.run_contextual_analysis()
        return analysis_result
    except Exception as e:
        print(f"Erreur lors de l'analyse contextuelle de l'URL: {e}")
        raise HTTPException(status_code=500, detail=f"Une erreur interne est survenue: {str(e)}")

@app.post("/api/url/predict")
def get_url_prediction(request: URLAnalyzeRequest):
    """
    Endpoint pour la prédiction 'machine'.
    Analyse une URL et renvoie le verdict du modèle de Machine Learning.
    """
    try:
        orchestrator = URLOrchestrator(request.url)
        prediction_result = orchestrator.run_prediction()
        return prediction_result
    except Exception as e:
        print(f"Erreur lors de la prédiction pour l'URL: {e}")
        raise HTTPException(status_code=500, detail=f"Une erreur interne est survenue: {str(e)}")
    

# -----------------------------------------------------------------------------
# ------ Nouveaux Endpoints pour le Dashboard -------
# -----------------------------------------------------------------------------
# On utilise `response_model` pour garantir que la sortie de l'API correspondra au schéma
@app.get("/api/dashboard/summary", response_model=DashboardResponse)
def get_dashboard_data(
    db: Session = Depends(get_db),
    period: str = "7d", # On garde une valeur par défaut
    start_date: Optional[str] = None, # Date de début personnalisée
    end_date: Optional[str] = None # Date de fin personnalisée
):
    """
    Endpoint principal pour le dashboard.
    Accepte une période prédéfinie ('today', '7d', '30d') ou une plage de dates personnalisée.
    """
    try:
        # On passe tous les paramètres au service, qui contiendra la logique
        summary_data = dashboard_service.get_dashboard_summary(
            db=db,
            period=period,
            custom_start_date=start_date,
            custom_end_date=end_date
        )
        return summary_data
    except Exception as e:
        print(f"Erreur lors de la génération du résumé du dashboard: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")
    

# -----------------------------------------------------------------------------
# ------ Nouveaux Endpoints pour l'Analyse des En-têtes -------
# -----------------------------------------------------------------------------
@app.post("/api/analyze/header")
def analyze_raw_header(request: HeaderAnalyzeRequest):
    """
    Analyse un en-tête d'e-mail brut fourni dans le corps de la requête.
    """
    try:
        # On instancie notre nouvel orchestrateur
        header_orchestrator = HeaderOrchestrator()
        final_report = header_orchestrator.run_header_analysis(request.raw_header)
        return final_report
    except Exception as e:
        print(f"Erreur lors de l'analyse du header brut: {e}")
        # Pour le débogage, il peut être utile d'imprimer l'exception
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Une erreur interne est survenue: {str(e)}")



# ==============================================================================
# 5. DÉMARRAGE DU SERVEUR
# ==============================================================================
if __name__ == "__main__":
    print("Démarrage du serveur PhishGard-AI sur http://127.0.0.1:8000")
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    # Pour un rechargement automatique lors des modifications de code, utilisez :
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)