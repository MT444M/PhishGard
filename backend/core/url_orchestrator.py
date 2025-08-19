# PhishGard-AI/core/url_orchestrator.py

import pandas as pd
from datetime import datetime
from joblib import load
import logging

from config import settings
from url_analysis import (
    domain_whois,
    ssl_hosting,
    static_content_extractor,
    dynamic_content_extractor,
    feature_derivation
)

# Configuration du logging pour une meilleure visibilité dans une API
logging.basicConfig(level=logging.INFO)

class URLOrchestrator:
    """
    Orchestre la collecte de données d'une URL pour l'analyse contextuelle et la prédiction de phishing.
    """
    REQUIRED_FEATURES = [
        "LengthOfURL", "URLComplexity", "CharacterComplexity", "DomainLengthOfURL", "IsDomainIP", "TLD", "TLDLength",
        "LetterCntInURL", "URLLetterRatio", "DigitCntInURL", "URLDigitRatio", "EqualCharCntInURL", "QuesMarkCntInURL",
        "AmpCharCntInURL", "OtherSpclCharCntInURL", "URLOtherSpclCharRatio", "NumberOfHashtags", "NumberOfSubdomains",
        "HavingPath", "PathLength", "HavingQuery", "HavingFragment", "HavingAnchor", "HasSSL", "IsUnreachable",
        "LineOfCode", "LongestLineLength", "HasTitle", "HasFavicon", "HasRobotsBlocked", "IsResponsive",
        "IsURLRedirects", "IsSelfRedirects", "HasDescription", "HasPopup", "HasIFrame", "IsFormSubmitExternal",
        "HasSocialMediaPage", "HasSubmitButton", "HasHiddenFields", "HasPasswordFields", "HasBankingKey",
        "HasPaymentKey", "HasCryptoKey", "HasCopyrightInfoKey ", "CntImages", "CntFilesCSS", "CntFilesJS",
        "CntSelfHRef", "CntEmptyRef", "CntExternalRef", "CntPopup", "CntIFrame", "UniqueFeatureCnt",
        "ShannonEntropy", "FractalDimension", "KolmogorovComplexity", "HexPatternCnt", "Base64PatternCnt"
    ]

    def __init__(self, url):
        self.url = url
        self.features = {}
        self.domain = domain_whois.parse_domain(url).get("Domain", "")

    # --- Fonctions de nettoyage privées ---
    def _format_datetime(self, dt):
        """Convertit un objet datetime en chaîne ISO 8601 ou retourne None."""
        return dt.isoformat() if isinstance(dt, datetime) else None

    def _format_issuer(self, issuer):
        """Simplifie la structure de l'émetteur du certificat en une chaîne plus robuste."""
        if not issuer or not isinstance(issuer, tuple):
            return "N/A"
        
        try:
            # Cette nouvelle logique parcourt toutes les parties du tuple 
            # pour construire un dictionnaire, ce qui est plus fiable.
            issuer_dict = {}
            for part in issuer:
                for key, value in part:
                    issuer_dict[key] = value
            
            org = issuer_dict.get('organizationName', '')
            cn = issuer_dict.get('commonName', '')
            country = issuer_dict.get('countryName', '')

            # On privilégie le nom le plus descriptif (commonName ou organizationName)
            main_name = cn or org
            if main_name and country:
                return f"{main_name} ({country})"
            return main_name or "N/A"

        except (ValueError, TypeError):
            # Fallback si la structure est vraiment inattendue
            return str(issuer)
            
    def _format_status_list(self, status_list):
        """Nettoie la liste de statuts WHOIS en retirant les URLs."""
        if not isinstance(status_list, list):
            return status_list
        return [s.split(' ')[0] for s in status_list]

    # --- MÉTHODE PUBLIQUE 1 : Analyse Contextuelle (Mise à jour) ---
    def run_contextual_analysis(self) -> dict:
        """
        Orchestre la collecte et le formatage des données contextuelles.
        """
        logging.info(f"Début de l'analyse contextuelle pour {self.url}")

        # 1. Collecter toutes les informations brutes
        whois_data = domain_whois.get_whois_info(self.domain)
        dns_data = domain_whois.get_passive_dns(self.domain)
        ssl_data = ssl_hosting.get_ssl_info(self.domain)
        geo_data = ssl_hosting.get_ip_geolocation_info(self.domain)
        content_data_static = static_content_extractor.extract_static_features(self.url)
        content_data_dynamic = dynamic_content_extractor.extract_dynamic_features(self.url)

        # 2. Enrichir les données WHOIS avec les informations ASN
        if geo_data.get("IPAddresses"):
            ip = geo_data["IPAddresses"][0]
            asn_info = domain_whois.get_asn_info(ip)
            whois_data.update(asn_info)
        
        # 3. Nettoyer et formater les données
        whois_data['CreationDate'] = self._format_datetime(whois_data.get('CreationDate'))
        whois_data['ExpirationDate'] = self._format_datetime(whois_data.get('ExpirationDate'))
        whois_data['UpdatedDate'] = self._format_datetime(whois_data.get('UpdatedDate'))
        whois_data['Status'] = self._format_status_list(whois_data.get('Status'))

        ssl_data['ValidFrom'] = self._format_datetime(ssl_data.get('ValidFrom'))
        ssl_data['ValidTo'] = self._format_datetime(ssl_data.get('ValidTo'))
        ssl_data['CertIssuer'] = self._format_issuer(ssl_data.get('CertIssuer'))

        # 4. Créer la section "Overview" avec une logique de fallback
        overview_country = whois_data.get("Country") or geo_data.get("Geolocation", {}).get("Country", "N/A")

        overview = {
            "label": "Overview",
            "data": {
                "domain": self.domain,
                "resolved_ip": geo_data.get("IPAddresses", []),
                "country": overview_country,
                "domain_age": str(whois_data.get("DomainAge", "N/A")),
                "https": "✅ Valid" if ssl_data.get('HasSSL') else "❌ Invalid",
                "blacklist": "N/A"
            }
        }

        # 4. Structurer la sortie finale
        return {
            "overview": overview,
            "domain_whois": {"label": "Domain & WHOIS", "data": whois_data},
            "dns": {"label": "DNS", "data": dns_data},
            "ssl_hosting": {"label": "SSL & Hosting", "data": ssl_data},
            "server_location": {"label": "Server Location", "data": geo_data.get("Geolocation", {})},
            "content": {"label": "Content", "data": {**content_data_static, **content_data_dynamic}},

        }


    # --- MÉTHODE PUBLIQUE 2 : Prédiction ML ---
    def run_prediction(self) -> dict:
        """
        Orchestre le pipeline complet de prédiction ML.
        """
        logging.info(f"Début de la prédiction ML pour {self.url}")
        
        # 1. Collecter uniquement les features nécessaires pour le modèle
        self._collect_ml_features()

        # 2. Préparer le vecteur de features et faire la prédiction
        return self._make_prediction()

    # --- Méthodes internes (helpers) ---
    def _collect_ml_features(self):
        """Collecte les caractéristiques requises par le modèle ML."""
        logging.info("[1/4] Analyse du domaine...")
        self.features.update(domain_whois.parse_domain(self.url))

        logging.info("[2/4] Analyse SSL...")
        ssl_info = ssl_hosting.get_ssl_info(self.domain)
        self.features['HasSSL'] = 1 if 'error' not in ssl_info else 0

        logging.info("[3/4] Extraction des contenus statiques et dynamiques...")
        static_feats = static_content_extractor.extract_static_features(self.url)
        dynamic_feats = dynamic_content_extractor.extract_dynamic_features(self.url)
        dynamic_feats.pop("ExternalLinks", None)
        self.features.update(static_feats)
        self.features.update(dynamic_feats)
        
        logging.info("[4/4] Dérivation des caractéristiques statistiques...")
        self.features.update(feature_derivation.derive_features(self.url))
        
    def _make_prediction(self):
        """Prépare le vecteur de données et retourne la prédiction du modèle."""
        logging.info("Préparation des données pour le modèle ML...")
        try:
            tld_df = pd.read_csv(settings.TLD_FREQ_PATH, index_col=0)
            tld_mapping = tld_df["Frequency"].to_dict()
        except FileNotFoundError:
            return {"error": f"Fichier TLD non trouvé: {settings.TLD_FREQ_PATH}"}

        feature_vector = {
            key: tld_mapping.get(self.features.get("TLD", ""), 0) if key == "TLD" else self.features.get(key, 0)
            for key in self.REQUIRED_FEATURES
        }
        
        input_df = pd.DataFrame([feature_vector])

        try:
            model = load(settings.URL_MODEL_PATH)
        except FileNotFoundError:
            return {"error": f"Modèle non trouvé: {settings.URL_MODEL_PATH}"}
        
        logging.info("Prédiction en cours...")
        prediction_val = model.predict(input_df)[0]
        probability = model.predict_proba(input_df)[0]
        
        is_phishing = prediction_val == 0 # Ajustez si 1 = phishing
        proba_phishing = probability[0] if is_phishing else probability[1]

        # Calculer le niveau de risque
        if is_phishing and proba_phishing > 0.75:
            risk_level = "High Risk"
        elif is_phishing:
            risk_level = "Medium Risk"
        else:
            risk_level = "Low Risk"

        return {
            "prediction": 0 if is_phishing else 1,
            "verdict": "⚠️ Phishing" if is_phishing else "✅ Legitimate",
            "confidence": f"{proba_phishing:.2%}",
            "risk_level": risk_level,
            "probability": {
                "phishing": f"{probability[0]:.2%}",
                "legitimate": f"{probability[1]:.2%}"
            }
        }
    

# test 
if __name__ == "__main__":
    import json
    url = "https://github.com/"
    orchestrator = URLOrchestrator(url)
    # Run contextual analysis
    result = orchestrator.run_contextual_analysis()
    print(json.dumps(result['overview'], indent=2))

    # result = orchestrator.run_prediction()
    # print(json.dumps(result, indent=2))