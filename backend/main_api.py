# backend/main_api.py

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import json
import os

# --- Import de vos modules d'analyse ---
# Nous ajustons les imports pour qu'ils fonctionnent depuis le dossier backend/
from core.email_orchestrator import EmailOrchestrator
from core.url_orchestrator import URLOrchestrator
from core import email_client # On garde l'authentification

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

# ==============================================================================
# 3. INITIALISATION DES ORCHESTRATEURS
# ==============================================================================
# On les initialise une seule fois au démarrage pour plus d'efficacité
email_orchestrator = EmailOrchestrator()
# Le client gmail est nécessaire pour l'orchestrateur d'email
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
    Endpoint pour récupérer la liste des emails à afficher dans le tableau de bord.
    POUR L'INSTANT: Renvoie des données de maquette.
    PLUS TARD: Pourra appeler `email_client.get_emails()` pour des données réelles.
    """
    # Ces données correspondent à votre maquette
    mock_emails = [
        {"id": "1", "sender": "security@paypaI-verify.com", "subject": "Action requise : Vérification de votre compte PayPal", "preview": "Votre compte a été temporairement suspendu...", "timestamp": "Il y a 2 heures", "verdict": "Phishing", "confidence": "94%"},
        {"id": "2", "sender": "noreply@amazon.com", "subject": "Votre commande a été expédiée", "preview": "Bonjour, votre commande #123456789 a été expédiée...", "timestamp": "Il y a 4 heures", "verdict": "Suspicious", "confidence": "67%"},
        {"id": "3", "sender": "notification@github.com", "subject": "[GitHub] Nouvelle pull request sur votre repository", "preview": "Une nouvelle pull request a été soumise par john.doe...", "timestamp": "Il y a 6 heures", "verdict": "Legitime", "confidence": "12%"},
        {"id": "4", "sender": "admin@microsoft-security.net", "subject": "Alerte de sécurité Microsoft - Connexion suspecte", "preview": "Nous avons détecté une connexion suspecte...", "timestamp": "Hier", "verdict": "Phishing", "confidence": "91%"}
    ]
    return mock_emails

@app.post("/api/analyze/url")
def analyze_url(request: URLAnalyzeRequest):
    """
    Analyse une URL fournie et renvoie la prédiction du modèle ML.
    """
    try:
        url_orchestrator = URLOrchestrator(request.url)
        url_orchestrator.collect_all_features()
        prediction_result = url_orchestrator.get_prediction()
        return prediction_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/email")
def analyze_email(request: EmailAnalyzeRequest):
    """
    Analyse un email complet en utilisant son ID.
    """
    if not gmail_service:
        raise HTTPException(status_code=503, detail="Service Gmail non disponible.")
    
    try:
        # 1. Récupérer l'email complet via l'API Gmail
        # Note : get_emails renvoie une liste, on prend le premier
        email_data_list = email_client.get_emails(gmail_service, email_id=request.email_id)
        if not email_data_list:
            raise HTTPException(status_code=404, detail=f"Email avec l'ID {request.email_id} non trouvé.")
        
        email_data = email_data_list[0]
        
        # 2. Lancer l'analyse complète via l'orchestrateur
        final_report = email_orchestrator.run_full_analysis(email_data)
        
        return final_report
    except Exception as e:
        # Pour le débuggage, il est utile d'imprimer l'erreur côté serveur
        print(f"Erreur lors de l'analyse de l'email: {e}")
        raise HTTPException(status_code=500, detail=f"Une erreur interne est survenue: {e}")


# ==============================================================================
# 5. DÉMARRAGE DU SERVEUR
# ==============================================================================
if __name__ == "__main__":
    print("Démarrage du serveur PhishGard-AI sur http://127.0.0.1:8000")
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    # Pour un rechargement automatique lors des modifications de code, utilisez :
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)