# PhishGard-AI/core/email_orchestrator.py

import re

# --- AJOUTS POUR LA BASE DE DONNÉES ---
from sqlalchemy.orm import Session
from database import crud

from core import email_client
# -----------------------------------------

# Importe tous nos modules d'analyse spécialisés
from email_analysis import header_parser, heuristic_analyzer, osint_enricher, llm_analyzer
from core.url_orchestrator import URLOrchestrator
from core.final_aggregator import FinalAggregator
from config.logging_config import get_logger

logger = get_logger(__name__)

def extract_urls_from_body(body_text):
    """Extrait toutes les URLs uniques d'un texte."""
    if not body_text:
        return []
    url_pattern = re.compile(r'https?://[^"\s\'<>]*')
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
    def run_full_analysis(self, email_data: dict, gmail_service, user_id: str):
        """
        Exécute le pipeline d'analyse complet, avec vérification du cache
        et sauvegarde en base de données.
        """
        email_id = email_data.get('id')
        logger.info(f"--- Début de l'orchestration pour l'e-mail ID: {email_id} ---")

        # 1. VÉRIFICATION DU CACHE EN BASE DE DONNÉES
        cached_analysis = crud.get_analysis_by_gmail_id(self.db, gmail_id=email_id, user_id=user_id)
        if cached_analysis:
            logger.info("Analyse trouvée en cache. Retour du résultat existant.")
            # On reconstruit un rapport final à partir des données de la BDD
            return {
                "id_email": email_id,
                "phishgard_verdict": cached_analysis.phishgard_verdict,
                "confidence_score": f"{cached_analysis.confidence_score}%",
                "final_score_internal": cached_analysis.confidence_score,
                "summary": "Résultat chargé depuis le cache de la base de données.",
                "breakdown": cached_analysis.breakdown
            }
        
        logger.info("Aucune analyse en cache. Lancement du pipeline complet.")

        # 2. PIPELINE D'ANALYSE (si pas de cache)
        logger.info("[1/5] Parsing des en-têtes...")
        parsed_headers = header_parser.parse_email_headers(email_data.get('full_headers', []))
        
        logger.info("[2/5] Lancement de l'enrichissement OSINT...")
        osint_results = osint_enricher.enrich_with_osint_data(parsed_headers)

        logger.info("[3/5] Lancement de l'analyse heuristique...")
        heuristic_results = heuristic_analyzer.analyze_header_heuristics(parsed_headers, osint_results)

        logger.info("[4/5] Lancement de l'analyse par le LLM...")
        llm_input = { "sender": email_data.get("sender"), "subject": email_data.get("subject"), "body": email_data.get("body") }
        llm_results = self.llm_analyzer_instance.analyze(llm_input)
        
        logger.info("[5/5] Extraction et analyse des URLs...")
        extracted_urls = extract_urls_from_body(email_data.get('body'))
        
        url_model_results = {"prediction": "N/A", "details": "Aucune URL trouvée dans l'e-mail."}
        if extracted_urls:
            first_url = extracted_urls[0]
            logger.info(f"Analyse de la première URL : {first_url}")
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
            logger.info("Aucune URL trouvée.")

        # 3. AGRÉGATION FINALE
        logger.info("[FIN] Agrégation de tous les résultats...")
        aggregator = FinalAggregator(
            heuristic_results=heuristic_results,
            url_model_results=url_model_results,
            llm_results=llm_results,
            osint_results=osint_results,
            email_id=email_id
        )
        final_report = aggregator.calculate_final_verdict()
        logger.info("--- Analyse complète terminée. ---")

        # 4. SAUVEGARDE DU NOUVEAU RAPPORT EN BASE DE DONNÉES
        logger.info(f"[SAVE] Sauvegarde du nouveau rapport pour l'ID: {email_id} en base de données.")

        # debug
        logger.debug(f"snippet: {email_data.get('snippet')}")
        crud.create_email_and_analysis(
            db=self.db,
            email_data=email_data,
            analysis_report=final_report,
            user_id=user_id
        )
        logger.info("Sauvegarde réussie.")

        # 5. NOUVEAU: APPLICATION DU LIBELLÉ SUR GMAIL
        verdict = final_report.get("phishgard_verdict")
        if verdict and verdict != "UNPROCESSED":
            logger.info(f"[LABEL] Début du processus d'étiquetage pour le verdict: {verdict}")
            try:
                # Obtenir l'ID du libellé (le crée s'il n'existe pas)
                label_id = email_client.get_or_create_label_id(gmail_service, verdict)
                # Appliquer le libellé à l'e-mail
                email_client.apply_label_to_email(gmail_service, email_id, label_id)
            except Exception as e:
                # On ne veut pas que l'API échoue si l'étiquetage rate
                logger.error(f"[LABEL] ERREUR: Le processus d'étiquetage a échoué : {e}")


        return final_report
