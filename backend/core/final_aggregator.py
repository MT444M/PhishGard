# PhishGard-AI/core/final_aggregator.py

from config import settings

class FinalAggregator:
    # Les poids sont maintenant chargés depuis la configuration
    WEIGHTS = settings.FINAL_VERDICT_WEIGHTS

    def __init__(self, heuristic_results, url_model_results, llm_results, osint_results, email_id=None):
        # On ajoute les résultats OSINT pour les règles de véto
        self.heuristic_results = heuristic_results
        self.url_model_results = url_model_results
        self.llm_results = llm_results
        self.osint_results = osint_results
        self.email_id = email_id
        self.final_score = 0
        self.final_classification = "UNPROCESSED"
        self.veto_applied = False
        self.veto_reason = ""

    # ... (la méthode _normalize_scores reste la même) ...
    def _normalize_scores(self):
        """Convertit les scores de chaque module sur une échelle de -100 à +100."""
        
        # 1. Normalisation du score heuristique
        score_h = self.heuristic_results.get("summary", {}).get("score", 0)
        # On peut rendre la normalisation un peu plus robuste
        normalized_score_h = min(100, max(-100, score_h * 2.5))

        # 2. Normalisation du score du modèle URL
        prob_phishing_str = self.url_model_results.get("probability_phishing", "0.0%")
        # Gérer le cas où la clé n'existe pas ou est invalide
        try:
            if prob_phishing_str and prob_phishing_str != "N/A":
                prob_phishing = float(prob_phishing_str.strip('%'))
            else:
                prob_phishing = 50.0 # Neutre si non disponible
        except (ValueError, TypeError):
            prob_phishing = 50.0 # Valeur par défaut en cas d'erreur
        normalized_score_url = 100 - (2 * prob_phishing)
        
        # 3. Normalisation du score du LLM
        llm_class = self.llm_results.get("classification", "LEGITIME")
        llm_conf_str = self.llm_results.get("confidence_score", "0")
        try:
            llm_conf = int(llm_conf_str)
        except (ValueError, TypeError):
            llm_conf = 0 # Valeur par défaut en cas d'erreur
        magnitude = llm_conf * 10
        normalized_score_llm = -magnitude if llm_class == 'PHISHING' else magnitude
        
        return normalized_score_h, normalized_score_url, normalized_score_llm


    def calculate_final_verdict(self):
        """Calcule le score final pondéré et détermine le verdict."""
        if self._apply_veto_rules():
            return self._build_report()

        norm_h, norm_url, norm_llm = self._normalize_scores()

        self.final_score = (norm_h * self.WEIGHTS["heuristic"]) + \
                           (norm_url * self.WEIGHTS["url_model"]) + \
                           (norm_llm * self.WEIGHTS["llm"])
        
        # ... (le reste de la logique de classification) ...
        if self.final_score > 40:
             self.final_classification = "Legitime"
        elif self.final_score < -40:
             self.final_classification = "Phishing"
        else:
             self.final_classification = "Suspicious"
        return self._build_report()

    def _apply_veto_rules(self):
        """Applique des règles de décision basées sur des preuves fortes (OSINT)."""
        # Règle 1: Domaine très récent
        for domain, data in self.osint_results.get("domain_analysis", {}).items():
            age = data.get("age_days", 999)
            if 0 <= age < 2: # Moins de 2 jours
                self.final_classification = "Phishing"
                self.final_score = -100
                self.veto_applied = True
                self.veto_reason = f"Veto: Le domaine '{domain}' est extrêmement récent ({age} jour(s))."
                return True
        
        # Règle 2: IP avec très mauvaise réputation
        for ip_data in self.osint_results.get("ip_analysis", []):
            abuse_score = ip_data.get("abuseipdb", {}).get("abuseConfidenceScore", 0)
            if abuse_score > 90:
                self.final_classification = "Phishing"
                self.final_score = -100
                self.veto_applied = True
                self.veto_reason = f"Veto: L'IP '{ip_data['ip']}' a un score de réputation très élevé ({abuse_score}%)."
                return True
        
        return False

    def _build_report(self):
        """Construit le dictionnaire de rapport final."""
        # Gestion des cas où le score final pourrait être NaN
        final_score = self.final_score
        if final_score != final_score:  # Vérifie si c'est NaN
            final_score = 0.0
            
        report = {
            "id_email": self.email_id,
            "phishgard_verdict": self.final_classification,
            "confidence_score": f"{round(abs(final_score), 2)}%",
            "final_score_internal": round(final_score, 2),
            "summary": "Agrégation des analyses heuristique, URL et LLM."
        }
        if self.veto_applied:
            report["summary"] = self.veto_reason
        
        # Ajout des résultats détaillés de chaque module
        report["breakdown"] = {
             "heuristic_analysis": self.heuristic_results,
             "url_ml_analysis": self.url_model_results,
             "llm_analysis": self.llm_results,
             "osint_enrichment": self.osint_results
        }
        return report
