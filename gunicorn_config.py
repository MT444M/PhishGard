"""
Configuration de Gunicorn pour PhishGard API
Fichier de configuration explicite pour résoudre les problèmes de proxy
"""
import os
import multiprocessing

# Paramètres du serveur
bind = "0.0.0.0:8000"  # Écoute sur toutes les interfaces
workers = multiprocessing.cpu_count() * 2 + 1  # Nombre recommandé de workers
worker_class = "uvicorn.workers.UvicornWorker"  # Utilise des workers uvicorn pour FastAPI

# Paramètres de logging
accesslog = "-"  # Log d'accès vers stdout
errorlog = "-"   # Log d'erreurs vers stderr
loglevel = "info"

# Paramètres de timeout
timeout = 120  # Augmente le timeout pour éviter les déconnexions prématurées
keepalive = 65  # Garde la connexion ouverte plus longtemps

# Autres paramètres
forwarded_allow_ips = "*"  # Permet les en-têtes X-Forwarded-* de tous les IPs
secure_scheme_headers = {
    'X-Forwarded-Proto': 'https',
}

# Configuration spécifique à Coolify
proxy_allow_ips = "*"
proxy_protocol = True  # Support du protocole PROXY si utilisé

# Pour le débogage
preload_app = True  # Charge l'application en mémoire avant de démarrer les workers
capture_output = True  # Capture stdout/stderr pour les inclure dans les logs
