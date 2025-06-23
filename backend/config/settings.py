# PhishGard-AI/config/settings.py

import os
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
load_dotenv()

# --- Configuration Gmail ---
# Porté des permissions pour l'API Gmail
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
# Chemin vers les fichiers de credentials
CREDENTIALS_FILE = 'client_secret.json'
TOKEN_FILE = 'token.json'

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