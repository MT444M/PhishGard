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
# IMPORTANT : Vous devez créer des identifiants OAuth 2.0 pour une "Application Web"
# dans la console Google Cloud (https://console.cloud.google.com/apis/credentials)
# et ajouter http://localhost:8000/api/auth/callback comme URI de redirection autorisé.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://localhost:8000/api/auth/callback"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"



# --- Configuration de l'application Frontend ---
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")



# --- Configuration du chiffrement ---
# Clé pour chiffrer/déchiffrer les tokens OAuth en base de données.
# Générez une clé sécurisée UNE SEULE FOIS avec la commande :
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Et stockez-la dans votre fichier .env
FERNET_KEY = os.getenv("FERNET_KEY")

# --- Configuration JWT (JSON Web Token) ---
# Clé secrète pour signer les JWT. À garder absolument secrète.
# Générez une clé avec : openssl rand -hex 32
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "a_very_secret_key_that_should_be_in_env_file")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 heures


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