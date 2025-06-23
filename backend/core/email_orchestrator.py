#   ---------------------------------------------------------------
# PhishGard-AI/core/email_orchestrator.py

import re #  Pour les expressions régulières
import json

# Importe tous nos modules d'analyse spécialisés
from email_analysis import header_parser, heuristic_analyzer, osint_enricher, llm_analyzer

# === NOUVEAUX IMPORTS pour connecter les deux mondes ===
from core.url_orchestrator import URLOrchestrator
from core.final_aggregator import FinalAggregator
# =======================================================


def extract_urls_from_body(body_text):
    """
    Extrait toutes les URLs uniques d'un texte en utilisant une expression régulière.
    """
    if not body_text:
        return []
    # Regex pour trouver les URLs http, https.
    url_pattern = re.compile(r'https?://[^\s"\'<>]+')
    urls = url_pattern.findall(body_text)
    # Retourner une liste d'URLs uniques
    return list(set(urls))


class EmailOrchestrator:
    """
    Orchestre les différentes étapes de l'analyse d'un e-mail.
    """
    def __init__(self):
        """Initialise les analyseurs nécessaires."""
        # Le LLMAnalyzer est plus lourd, on l'initialise ici
        self.llm_analyzer_instance = llm_analyzer.LLMAnalyzer()

    def run_full_analysis(self, email_data):
        """
        Exécute le pipeline d'analyse complet sur un e-mail.
        """
        print(f"\n--- Début de l'analyse complète pour l'e-mail ID: {email_data.get('id')} ---")
        
        full_report = {
            "email_summary": {
                "id": email_data.get('id'),
                "from": email_data.get('sender'),
                "subject": email_data.get('subject')
            },
            "analysis_results": {}
        }

        # --- ÉTAPES D'ANALYSE EXISTANTES ---
        print("[1/5] Parsing des en-têtes...")
        parsed_headers = header_parser.parse_email_headers(email_data.get('full_headers', []))
        
        print("[2/5] Lancement de l'enrichissement OSINT...")
        osint_results = osint_enricher.enrich_with_osint_data(parsed_headers)

        print("[3/5] Lancement de l'analyse heuristique...")
        heuristic_results = heuristic_analyzer.analyze_header_heuristics(parsed_headers, osint_results)

        print("[4/5] Lancement de l'analyse par le LLM...")
        llm_input = { "sender": email_data.get("sender"), "subject": email_data.get("subject"), "body": email_data.get("body") }
        llm_results = self.llm_analyzer_instance.analyze(llm_input)
        
        # --- NOUVELLE ÉTAPE : ANALYSE DES URLS DANS L'EMAIL ---
        print("[5/5] Extraction et analyse des URLs contenues dans l'e-mail...")
        extracted_urls = extract_urls_from_body(email_data.get('body'))
        full_report['analysis_results']['extracted_urls'] = extracted_urls # On stocke les URLs trouvées
        
        url_model_results = {"prediction": "N/A", "details": "Aucune URL trouvée dans l'e-mail."}
        if extracted_urls:
            first_url = extracted_urls[0]
            print(f"      ... Analyse de la première URL trouvée : {first_url}")
            url_orchestrator = URLOrchestrator(first_url)
            url_orchestrator.collect_all_features()
            url_model_results = url_orchestrator.get_prediction()
        else:
            print("      ... Aucune URL trouvée à analyser.")
        # ========================================================
        
        # On stocke tous les résultats intermédiaires avant l'agrégation
        full_report['analysis_results']['heuristic_analysis'] = heuristic_results
        full_report['analysis_results']['osint_enrichment'] = osint_results
        full_report['analysis_results']['llm_analysis'] = llm_results
        full_report['analysis_results']['url_model_analysis'] = url_model_results

        # --- DERNIÈRE ÉTAPE : AGRÉGATION FINALE ---
        print("\n[FIN] Agrégation de tous les résultats pour le verdict final...")
        aggregator = FinalAggregator(
            heuristic_results=heuristic_results,
            url_model_results=url_model_results,
            llm_results=llm_results,
            osint_results=osint_results
        )
        final_verdict_report = aggregator.calculate_final_verdict()
        print("--- Analyse complète terminée. ---")
        
        # Le rapport final de l'orchestrateur est maintenant le rapport de l'agrégateur
        return final_verdict_report