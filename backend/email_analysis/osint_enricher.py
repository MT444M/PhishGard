# PhishGard-AI/analysis/osint_enricher.py

import requests
import whois
from datetime import datetime
from dateutil import parser as dateutil_parser

# Suivant votre nouvelle architecture, les clés API sont dans un fichier de config
# qui est chargé dans l'objet settings.
from config import settings

# --- Fonctions de base (correctement refactorisées) ---

def get_ipinfo_data(ip_address):
    """Récupère les données de géolocalisation d'une IP via IPinfo.io."""
    if not settings.IPINFO_API_KEY:
        print("  [OSINT Avertissement] Clé API IPinfo non configurée.")
        return {"error": "Clé API IPinfo non configurée."}
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}?token={settings.IPINFO_API_KEY}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  [OSINT Erreur] Appel IPinfo échoué pour {ip_address}: {e}")
        return {"error": str(e)}

def get_abuseipdb_data(ip_address):
    """Vérifie la réputation d'une IP via AbuseIPDB."""
    if not settings.ABUSEIPDB_API_KEY:
        print("  [OSINT Avertissement] Clé API AbuseIPDB non configurée.")
        return {"error": "Clé API AbuseIPDB non configurée."}
    try:
        headers = {'Accept': 'application/json', 'Key': settings.ABUSEIPDB_API_KEY}
        params = {'ipAddress': ip_address, 'maxAgeInDays': '90'}
        response = requests.get("https://api.abuseipdb.com/api/v2/check", headers=headers, params=params, timeout=5)
        response.raise_for_status()
        return response.json().get("data", {})
    except requests.exceptions.RequestException as e:
        print(f"  [OSINT Erreur] Appel AbuseIPDB échoué pour {ip_address}: {e}")
        return {"error": str(e)}

def get_domain_age_info(domain_name):
    """Récupère la date de création d'un domaine via WHOIS."""
    try:
        domain_info = whois.whois(domain_name)
        creation_date = domain_info.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if creation_date:
            # S'assurer que la date est timezone-aware pour la comparaison si possible
            now = datetime.now(creation_date.tzinfo)
            age = now - creation_date
            return {"creation_date": creation_date.isoformat(), "age_days": age.days}
        return {"error": "Date de création non trouvée."}
    except Exception as e:
        print(f"  [OSINT Erreur] Recherche WHOIS échouée pour {domain_name}: {e}")
        return {"error": f"Erreur WHOIS: {str(e)}"}

# --- CORRECTION 1: Réintégration de l'analyse de chemin ---

def calculate_hop_delays(received_path_list):
    """
    Calcule les délais entre les sauts (hops).
    La fonction est restaurée à partir du script original.
    """
    delays_seconds = []
    # La liste received_path est du plus récent au plus ancien, on l'inverse pour le calcul.
    chronological_hops = list(reversed(received_path_list))

    for i in range(len(chronological_hops) - 1):
        try:
            timestamp_hop_i = chronological_hops[i].get("timestamp")
            timestamp_hop_i_plus_1 = chronological_hops[i+1].get("timestamp")

            if timestamp_hop_i and timestamp_hop_i_plus_1:
                dt_i = dateutil_parser.parse(timestamp_hop_i)
                dt_i_plus_1 = dateutil_parser.parse(timestamp_hop_i_plus_1)
                delay = (dt_i_plus_1 - dt_i).total_seconds()
                delays_seconds.append(round(delay))
            else:
                delays_seconds.append(None)
        except Exception as e:
            print(f"  [OSINT Erreur] Impossible de calculer le délai entre les sauts : {e}")
            delays_seconds.append(None)
    return delays_seconds

# --- Fonction principale d'enrichissement (corrigée et complétée) ---

def enrich_with_osint_data(parsed_headers):
    """
    Orchestre l'enrichissement OSINT à partir des en-têtes parsés,
    en incluant l'analyse de chemin et une collecte de domaines exhaustive.
    """
    # CORRECTION 1: Ajout de 'path_analysis' à la structure de résultats
    osint_results = {
        "ip_analysis": [],
        "domain_analysis": {},
        "path_analysis": {
            "hop_countries": [],
            "hop_delays_seconds": []
        }
    }

    # --- 1. Collecte des IPs et domaines uniques à analyser ---
    ips_to_analyze = set()
    if parsed_headers.get("x_originating_ip"):
        ips_to_analyze.add(parsed_headers["x_originating_ip"])
    for hop in parsed_headers.get("received_path", []):
        if hop.get("from_ip"):
            ips_to_analyze.add(hop["from_ip"])

    domains_to_analyze = set()
    # Adresses standard
    for key in ["from_address", "return_path", "reply_to_address"]:
        addr = parsed_headers.get(key)
        if addr and addr.get("domain"):
            domains_to_analyze.add(addr["domain"])
    
    # CORRECTION 2: Ajout des domaines des signatures DKIM
    for auth_res in parsed_headers.get("authentication_results_summary", []):
        parsed_vals = auth_res.get("parsed_values", {})
        for dkim in parsed_vals.get("dkim", []):
            if dkim.get("domain"):
                domains_to_analyze.add(dkim["domain"])

    # --- 2. Analyse des IPs ---
    ip_geo_cache = {}
    for ip in ips_to_analyze:
        print(f"  [OSINT] Analyse de l'IP : {ip}")
        ipinfo_data = get_ipinfo_data(ip)
        ip_data = {
            "ip": ip,
            "ipinfo": ipinfo_data,
            "abuseipdb": get_abuseipdb_data(ip)
        }
        osint_results["ip_analysis"].append(ip_data)
        # Mettre en cache la géolocalisation pour l'analyse de chemin
        if isinstance(ipinfo_data, dict) and ipinfo_data.get("country"):
            ip_geo_cache[ip] = ipinfo_data.get("country")

    # --- 3. Analyse des Domaines ---
    for domain in domains_to_analyze:
        print(f"  [OSINT] Analyse du domaine : {domain}")
        osint_results["domain_analysis"][domain] = get_domain_age_info(domain)

    # --- 4. CORRECTION 1: Exécution de l'Analyse de Chemin ---
    received_path = parsed_headers.get("received_path", [])
    
    # Construire la liste des pays des sauts
    hop_countries = []
    # Inverser pour l'ordre chronologique (source -> destination)
    for hop in reversed(received_path):
        ip = hop.get("from_ip")
        if ip in ip_geo_cache:
            hop_countries.append(ip_geo_cache[ip])
        elif ip: # IP privée ou locale non trouvée dans le cache
            hop_countries.append("LOCAL/UNKNOWN")

    osint_results["path_analysis"]["hop_countries"] = hop_countries
    
    # Calculer les délais entre les sauts
    osint_results["path_analysis"]["hop_delays_seconds"] = calculate_hop_delays(received_path)
        
    return osint_results