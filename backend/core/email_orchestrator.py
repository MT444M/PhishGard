# PhishGard-AI/core/email_orchestrator.py

import re
import json

# --- AJOUTS POUR LA BASE DE DONNÉES ---
from sqlalchemy.orm import Session
from database import crud
# -----------------------------------------

# Importe tous nos modules d'analyse spécialisés
from email_analysis import header_parser, heuristic_analyzer, osint_enricher, llm_analyzer
from core.url_orchestrator import URLOrchestrator
from core.final_aggregator import FinalAggregator


def extract_urls_from_body(body_text):
    """Extrait toutes les URLs uniques d'un texte."""
    if not body_text:
        return []
    url_pattern = re.compile(r'https?://[^\s"\'<>]+')
    urls = url_pattern.findall(body_text)
    return list(set(urls))


class EmailOrchestrator:
    """
    Orchestre les différentes étapes de l'analyse d'un e-mail,
    en incluant la communication avec la base de données.
    """
    # --- MODIFICATION DU CONSTRUCTEUR ---
    def __init__(self, db: Session):
        """
        Initialise les analyseurs nécessaires et stocke la session de base de données.
        """
        self.db = db
        self.llm_analyzer_instance = llm_analyzer.LLMAnalyzer()

    # --- MÉTHODE D'ANALYSE ENTIÈREMENT MISE À JOUR ---
    def run_full_analysis(self, email_data: dict):
        """
        Exécute le pipeline d'analyse complet, avec vérification du cache
        et sauvegarde en base de données.
        """
        email_id = email_data.get('id')
        print(f"\n--- Début de l'orchestration pour l'e-mail ID: {email_id} ---")

        # 1. VÉRIFICATION DU CACHE EN BASE DE DONNÉES
        print(f"[CACHE] Vérification de l'existence d'une analyse pour l'ID: {email_id}")
        cached_analysis = crud.get_analysis_by_gmail_id(self.db, gmail_id=email_id)
        if cached_analysis:
            print(f"      ... Analyse trouvée en cache. Retour du résultat existant.")
            # On reconstruit un rapport final à partir des données de la BDD
            return {
                "id_email": email_id,
                "phishgard_verdict": cached_analysis.phishgard_verdict,
                "confidence_score": f"{cached_analysis.confidence_score}%",
                "final_score_internal": cached_analysis.confidence_score,
                "summary": "Résultat chargé depuis le cache de la base de données.",
                "breakdown": cached_analysis.breakdown
            }
        
        print("      ... Aucune analyse en cache. Lancement du pipeline complet.")

        # 2. PIPELINE D'ANALYSE (si pas de cache)
        print("[1/5] Parsing des en-têtes...")
        parsed_headers = header_parser.parse_email_headers(email_data.get('full_headers', []))
        
        print("[2/5] Lancement de l'enrichissement OSINT...")
        osint_results = osint_enricher.enrich_with_osint_data(parsed_headers)

        print("[3/5] Lancement de l'analyse heuristique...")
        heuristic_results = heuristic_analyzer.analyze_header_heuristics(parsed_headers, osint_results)

        print("[4/5] Lancement de l'analyse par le LLM...")
        llm_input = { "sender": email_data.get("sender"), "subject": email_data.get("subject"), "body": email_data.get("body") }
        llm_results = self.llm_analyzer_instance.analyze(llm_input)
        
        print("[5/5] Extraction et analyse des URLs...")
        extracted_urls = extract_urls_from_body(email_data.get('body'))
        
        url_model_results = {"prediction": "N/A", "details": "Aucune URL trouvée dans l'e-mail."}
        if extracted_urls:
            first_url = extracted_urls[0]
            print(f"      ... Analyse de la première URL : {first_url}")
            url_orchestrator = URLOrchestrator(first_url)
            # Note: Assurez-vous que vos méthodes dans URLOrchestrator sont accessibles si préfixées par `_`
            # Idéalement, elles devraient être publiques : .collect_ml_features() et .make_prediction()
            prediction_data = url_orchestrator.run_prediction()
            url_model_results = {
                "verdict": prediction_data.get("verdict"),
                "confidence": prediction_data.get("confidence"),
                "details": [{"url": first_url, **prediction_data}]
            }
        else:
            print("      ... Aucune URL trouvée.")

        # 3. AGRÉGATION FINALE
        print("\n[FIN] Agrégation de tous les résultats...")
        aggregator = FinalAggregator(
            heuristic_results=heuristic_results,
            url_model_results=url_model_results,
            llm_results=llm_results,
            osint_results=osint_results,
            email_id=email_id
        )
        final_report = aggregator.calculate_final_verdict()
        print("--- Analyse complète terminée. ---")

        # 4. SAUVEGARDE DU NOUVEAU RAPPORT EN BASE DE DONNÉES
        print(f"[SAVE] Sauvegarde du nouveau rapport pour l'ID: {email_id} en base de données.")

        # debug
        print(f"snippet: {email_data.get('snippet')}")
        crud.create_email_and_analysis(
            db=self.db,
            email_data=email_data,
            analysis_report=final_report
        )
        print("      ... Sauvegarde réussie.")

        return final_report