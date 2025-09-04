# PhishGard - AI-Powered Phishing Analysis Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/MT444M/PhishGard)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PhishGard est une plateforme avancée conçue pour automatiser la détection, l'analyse et la réponse aux menaces de phishing. En combinant l'analyse par des modèles de langage (LLM) locaux, l'enrichissement via des sources de renseignement ouvertes (OSINT) et des analyses heuristiques approfondies, PhishGard fournit une évaluation complète du risque pour chaque email et URL suspect.

**Dépôts de code source :**
- **GitHub:** [https://github.com/MT444M/PhishGard](https://github.com/MT444M/PhishGard)
- **GitLab:** [https://gitlab.usts.ai/mbaye/phishgard](https://gitlab.usts.ai/mbaye/phishgard)

## ✨ Fonctionnalités Principales

- **Analyse d'Email Complète** : Extraction et analyse des en-têtes, du corps du message et des pièces jointes.
- **Analyse d'URL Approfondie** :
    - Examen des certificats SSL et des informations d'hébergement.
    - Requêtes WHOIS pour identifier l'âge et le propriétaire du domaine.
    - Analyse de contenu statique et dynamique (rendu JavaScript).
    - Vérification de la réputation auprès de multiples flux de menaces.
- **Intelligence Artificielle (IA) Locale** : Utilise des modèles de langage (par défaut : **Qwen3 0.5B**) hébergés localement pour une analyse privée et sécurisée, détectant les signaux de phishing subtils.
- **Enrichissement OSINT** : Enrichit les données avec des informations provenant de sources externes pour une meilleure contextualisation de la menace.
- **Dashboard Web Intuitif** : Une interface utilisateur claire pour visualiser les analyses, gérer les emails et lancer des analyses à la demande.
- **Architecture Modulaire** : Le backend est conçu pour être extensible, permettant d'ajouter facilement de nouveaux modules d'analyse.
- **Containerisation** : Entièrement containerisé avec Docker pour un déploiement et une mise à l'échelle simplifiés.

## ⚙️ Architecture et Workflow

La plateforme fonctionne selon un workflow d'orchestration sophistiqué :

1.  **Réception de l'Email** : Un email est reçu via l'API ou une boîte de réception surveillée.
2.  **Orchestration Principale** : `EmailOrchestrator` prend le contrôle.
3.  **Analyse des En-têtes** : `HeaderOrchestrator` analyse les en-têtes (SPF, DKIM, DMARC, chemin de livraison).
4.  **Analyse des URLs** : `UrlOrchestrator` extrait toutes les URLs de l'email et lance des analyses en parallèle :
    - WHOIS, SSL, Hébergement (`domain_whois`, `ssl_hosting`).
    - Réputation et flux de menaces (`reputation_threat_feeds`).
    - Analyse de contenu (`static_content_extractor`, `dynamic_content_extractor`).
5.  **Analyses Complémentaires** : Simultanément, le système effectue :
    - Une analyse heuristique (`heuristic_analyzer`).
    - Une analyse par le LLM local (`llm_analyzer`).
    - Un enrichissement OSINT (`osint_enricher`).
6.  **Agrégation Finale** : `FinalAggregator` collecte tous les résultats, calcule un score de risque global et fournit un verdict final.
7.  **Restitution** : Les résultats sont stockés en base de données et affichés sur le dashboard.

## 🛠️ Stack Technique

-   **Backend**: Python, FastAPI
-   **Base de Données**: PostgreSQL, SQLAlchemy (ORM), Alembic (Migrations)
-   **Frontend**: HTML5, CSS3, Vanilla JavaScript
-   **IA / LLM**: Modèles locaux (Ollama, etc.)
-   **Containerisation**: Docker & Docker Compose
-   **Analyse Asynchrone**: `asyncio`

## 🚀 Démarrage Rapide

### Prérequis

-   [Docker](https://www.docker.com/get-started)
-   [Docker Compose](https://docs.docker.com/compose/install/)

### Installation

1.  **Clonez le dépôt :**
    ```bash
    # Via GitHub
    git clone https://github.com/MT444M/PhishGard.git
    
    # Ou via GitLab
    # git clone https://gitlab.usts.ai/mbaye/phishgard.git
    
    cd PhishGard
    ```

2.  **Configurez les variables d'environnement :**
    Copiez le fichier d'exemple. Toutes les configurations se trouvent maintenant à la racine du projet.
    ```bash
    cp .env.example .env
    ```
    Modifiez `.env` et remplissez les clés nécessaires :
    - `IPINFO_API_KEY`, `ABUSEIPDB_API_KEY` pour l'enrichissement OSINT.
    - `FERNET_KEY`, `JWT_SECRET_KEY` pour la sécurité. Vous pouvez en générer avec `openssl rand -hex 32`.
    - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` si vous souhaitez utiliser l'authentification Google.

3.  **Lancez l'application avec Docker Compose :**
    Cette commande construira les images Docker, démarrera les services (API, base de données) et lancera le serveur.
    ```bash
    docker-compose up --build
    ```

4.  **Appliquez les migrations de la base de données :**
    Dans un autre terminal, une fois que le conteneur est en cours d'exécution, exécutez :
    ```bash
    docker-compose exec backend alembic upgrade head
    ```

5.  **Accédez à l'application :**
    -   **Dashboard Web** : [http://localhost:80](http://localhost:80)
    -   **Documentation de l'API** (Swagger UI) : [http://localhost:8000/docs](http://localhost:8000/docs)

## 🚢 Déploiement

Pour des instructions de déploiement en production, veuillez vous référer au fichier [DEPLOYMENT.md](DEPLOYMENT.md).

## 🤝 Contribution

Les contributions sont les bienvenues ! Si vous souhaitez améliorer PhishGard, veuillez suivre ces étapes :

1.  Forkez le projet.
2.  Créez une nouvelle branche (`git checkout -b feature/nouvelle-fonctionnalite`).
3.  Commitez vos changements (`git commit -m 'Ajout de nouvelle-fonctionnalite'`).
4.  Pushez vers la branche (`git push origin feature/nouvelle-fonctionnalite`).
5.  Ouvrez une Pull Request.

## 📄 Licence

Ce projet est sous licence MIT.