PhishGard-AI/
│
├── config/
│   ├── __init__.py
│   ├── settings.py            # Clés API, chemins, configurations centrales
│
├── core/
│   ├── __init__.py
│   ├── email_client.py        # Gère TOUTE l'interaction avec l'API Gmail (auth, fetch, etc.)
│   ├── email_orchestrator.py # Le "cerveau" qui organise les analyses d'un e-mail 
|   └── url_orchestrator.py # Le "cerveau" qui organise les analyses d'une URL
    └── final_aggregator.py.    # la fusion des score de prediction
│
├── email_analysis/
│   ├── __init__.py
│   ├── header_parser.py       # Fonctions pour parser les en-têtes bruts
│   ├── heuristic_analyzer.py  # Logique d'analyse heuristique des en-têtes
│   ├── llm_analyzer.py        # Classe pour l'analyse par le LLM
│   └── osint_enricher.py      # Fonctions et classes pour l'enrichissement OSINT
|
├── url_analysis/                  # <== NOUVEAU
│   ├── __init__.py
│   ├── domain_whois.py        # Analyse du domaine et WHOIS
│   ├── feature_derivation.py        # Extraction de caractères et caractères complexes
│   ├── static_content_extractor.py    # Extraction de contenu statique
│   ├── dynamic_content_extractor.py    # Extraction de contenu dynamique
│   ├── reputation_threat_feeds.py      # Extraction de renseignements de renseignements de renseignements
│   └── ssl_hosting.py          # Analyse SSL/TLS et hosting
│
|
├── assets/                        # <== NOUVEAU
│   ├── model_RF.pkl             # Modèle RF pour le modèle de classification
│   └── tld_freq.csv             # Fichier CSV contenant la fréquence des TLD
|
│
├── main_api.py                    # Point d'entrée principal de l'application
│
├── requirements.txt           # Dépendances du projet
│
└── KEY.env               # Modèle pour les variables d'environnement (clés API)
