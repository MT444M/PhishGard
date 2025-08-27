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
│   └── url_orchestrator.py # Le "cerveau" qui organise les analyses d'une URL et  l'analyse contextuelle
    └── final_aggregator.py.    # la fusion des score de prediction

    auth/
    ├── __init__.py
    ├── auth_service.py           # Logique d'authentification
    └── auth_router.py            # Routes d'authentification

    alembic/
    ├── __init__.py
    ├── env.py                     # Configuration de l'environnement Alembic
    ├── script.py.mako             # Template pour les scripts de migration
    └── versions/                  # Dossier contenant les versions de migration

    dashboard/
    ├── __init__.py
    ├── dashboard_service.py        # Logique principale du tableau de bord
    └── schemas.py                   # Schéma de données pour le tableau de bord


├── database/                  
│   ├── __init__.py
│   ├── database.py            # Configuration et gestion des sessions DB
│   ├── models.py              # Définition des tables (schéma) via SQLAlchemy
│   └── crud.py                # Fonctions CRUD (Create, Read, Update, Delete)
│
├── email_analysis/
│   ├── __init__.py
│   ├── header_parser.py       # Fonctions pour parser les en-têtes bruts
│   ├── heuristic_analyzer.py  # Logique d'analyse heuristique des en-têtes
│   ├── llm_analyzer.py        # Classe pour l'analyse par le LLM
│   └── osint_enricher.py      # Fonctions et classes pour l'enrichissement OSINT

 static/
│   ├── __init__.py
│   ├── index.html              # Page d'accueil du frontend
│   ├── js/
│   │   ├── config.js           # Configuration JavaScript pour le frontend
│   │   └── ...
│   └── css/
│       ├── styles.css          # Styles CSS pour le frontend
│       └── ...
│
├── url_analysis/                  
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

├── alembic.ini                     # Configuration d'Alembic pour les migrations de base de données
│
├── requirements.txt           # Dépendances du projet
│
└── KEY.env               # Modèle pour les variables d'environnement (clés API)
