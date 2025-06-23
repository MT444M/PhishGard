# PhishGard-AI/core/url_orchestrator.py

import pandas as pd
from joblib import load

from config import settings
# Importer les extracteurs depuis leur nouvel emplacement
from url_analysis import (
    domain_whois,
    ssl_hosting,
    static_content_extractor,
    dynamic_content_extractor,
    feature_derivation
)

class URLOrchestrator:
    """
    Orchestre la collecte de caractéristiques d'une URL et la prédiction de phishing.
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

    def collect_all_features(self):
        """Collecte toutes les caractéristiques de l'URL en appelant les modules spécialisés."""
        print("[1/5] Analyse du domaine et WHOIS...")
        self.features.update(domain_whois.parse_domain(self.url))

        print("[2/5] Analyse SSL...")
        # La fonction get_ssl_info peut échouer, on gère le cas
        ssl_info = ssl_hosting.get_ssl_info(self.features.get("Domain", ""))
        self.features['HasSSL'] = 1 if 'error' not in ssl_info else 0

        print("[3/5] Extraction du contenu statique...")
        self.features.update(static_content_extractor.extract_static_features(self.url))

        print("[4/5] Extraction du contenu dynamique (via Selenium)...")
        dynamic_feats = dynamic_content_extractor.extract_dynamic_features(self.url)
        dynamic_feats.pop("ExternalLinks", None) # Exclure la liste des liens
        self.features.update(dynamic_feats)
        
        print("[5/5] Dérivation des caractéristiques statistiques...")
        self.features.update(feature_derivation.derive_features(self.url))
        
        return self.features

    def get_prediction(self):
        """Prépare les données et utilise le modèle RF pour obtenir une prédiction."""
        print("Préparation des données pour le modèle ML...")
        # Mapper la valeur TLD à sa fréquence
        try:
            tld_df = pd.read_csv(settings.TLD_FREQ_PATH, index_col=0)
            tld_mapping = tld_df["Frequency"].to_dict()
        except FileNotFoundError:
            return {"error": f"Fichier TLD non trouvé à l'emplacement : {settings.TLD_FREQ_PATH}"}

        # Construire le dictionnaire pour le DataFrame
        feature_vector = {}
        for key in self.REQUIRED_FEATURES:
            if key == "TLD":
                raw_tld = self.features.get("TLD", "")
                feature_vector[key] = tld_mapping.get(raw_tld, 0)
            else:
                # Utiliser 0 pour les caractéristiques manquantes
                feature_vector[key] = self.features.get(key, 0)
        
        input_df = pd.DataFrame([feature_vector])

        # Charger le modèle et prédire
        try:
            model = load(settings.URL_MODEL_PATH)
        except FileNotFoundError:
            return {"error": f"Modèle non trouvé à l'emplacement : {settings.URL_MODEL_PATH}"}
        
        print("Prédiction en cours...")
        prediction = model.predict(input_df)[0]
        probability = model.predict_proba(input_df)[0]
        
        return {
            "prediction": "phishing" if prediction == 1 else "legitimate",
            "probability_phishing": f"{probability[1]:.2%}",
            "probability_legitimate": f"{probability[0]:.2%}"
        }