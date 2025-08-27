# PhishGard-AI/config/settings.py

import os
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
load_dotenv()


# --- Définition des chemins de base ---
# BASE_DIR est le dossier racine du projet (PhishGard-AI/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# CONFIG_DIR est ce dossier (/config)
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
# On crée un dossier dédié pour les secrets et les tokens générés
SECRETS_DIR = os.path.join(CONFIG_DIR, '.secrets')


# --- Configuration OAuth 2.0 Google ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Récupérer l'hôte et le protocole pour construction des URLs
HOST = os.getenv("HOST", "localhost:8000")
# En production, on utilise HTTPS
ENV = os.getenv("ENV", "development")
PROTOCOL = "https" if ENV.lower() == "production" else "http"

# Construction des URLs avec variables d'environnement
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", f"{PROTOCOL}://{HOST}/api/auth/callback")
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"



# --- Configuration de l'application Frontend ---
# L'URL vers laquelle l'utilisateur est redirigé après une authentification réussie.
# Puisque le frontend est maintenant servi par le backend, on redirige vers la racine.
FRONTEND_URL = os.getenv("FRONTEND_URL", f"{PROTOCOL}://{HOST}/")



# --- Configuration du chiffrement ---
FERNET_KEY = os.getenv("FERNET_KEY")

# --- Configuration JWT (JSON Web Token) ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 heures


# --- Validation des secrets pour la production ---
if os.getenv("ENV") == "production":
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in production.")
    if not FERNET_KEY:
        raise ValueError("FERNET_KEY must be set in production.")
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be set in production.")


# --- Configuration Gmail ---
# Portée des permissions pour l'API Gmail (on remet toutes celles nécessaires)
GMAIL_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.email', # Pour récupérer l'email de l'utilisateur
    'https://www.googleapis.com/auth/userinfo.profile' # Pour récupérer le profil (et google_id)
]

# Chemin vers le fichier credentials téléchargé depuis Google Cloud
# Il doit être placé dans le dossier /config

# Chemin vers le fichier token qui sera généré dynamiquement
# Il sera stocké dans /config/.secrets/ pour éviter le reload du serveur

# --- Configuration du Modèle LLM ---
# Nom du modèle à utiliser pour l'analyse
LLM_MODEL_NAME = "Qwen/Qwen3-0.6B"

# Paramètres de génération par défaut pour le LLM
LLM_GENERATION_PARAMS = {
    "max_new_tokens": 100,
    "do_sample": True,
    "temperature": 0.1,
    "top_p": 0.9,
    "top_k": 50,
}

# --- Clés API pour l'enrichissement OSINT ---
# Les clés sont chargées depuis les variables d'environnement
IPINFO_API_KEY = os.getenv("IPINFO_API_KEY")
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY")



# --- Configuration de l'analyseur d'URL ---
# Chemin vers les assets du modèle ML
URL_MODEL_PATH = "assets/model_RF.pkl"
TLD_FREQ_PATH = "assets/tld_freq.csv"


# --- Configuration de l'Agrégateur Final ---
# Poids pour chaque module d'analyse dans le score final
FINAL_VERDICT_WEIGHTS = {
    "heuristic": 0.30,
    "url_model": 0.40,
    "llm": 0.30
}
