# PhishGard-AI/analysis/llm_analyzer.py

import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from config import settings # On garde l'import pour les configs par défaut
# import settings

class LLMAnalyzer:
    """
    Analyse le contenu d'un e-mail en utilisant un modèle de langage (LLM)
    pour le classifier comme phishing ou légitime, en se basant sur la logique du POC validé.
    """
    def __init__(self, model_name=None, generation_config=None):
        """
        Initialise le modèle et le tokenizer.
        Permet de surcharger la configuration centrale pour plus de flexibilité.
        """
        # --- CORRECTION 3: Rétablir la flexibilité de configuration ---
        # Utilise le nom du modèle passé en argument, sinon celui des settings.
        _model_name = model_name or settings.LLM_MODEL_NAME
        
        print(f"[LLM] Initialisation du modèle : {_model_name}...")
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                _model_name,
                torch_dtype="auto",
                device_map="auto"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(_model_name)
            print("[LLM] Modèle chargé avec succès.")
        except Exception as e:
            print(f"[LLM] Erreur lors du chargement du modèle : {e}")
            self.model = None
            self.tokenizer = None

        # --- CORRECTION 1: Rétablir le prompt original ---
        self.prompt_template = """
            Tu es un détecteur d'emails d'hameçonnage (phishing). Ton rôle est d'analyser l'email suivant pour déterminer s'il est légitime ou malveillant.

            EMAIL:
            De: {sender}
            Objet: {subject}
            Corps: {body}

            Les signes d'hameçonnage incluent:
            - Urgence ou menaces
            - Demandes d'informations personnelles
            - Liens/URLs suspects
            - Orthographe/grammaire incorrecte
            - Adresse d'expéditeur douteuse
            - Offres trop belles pour être vraies

            Réponds UNIQUEMENT avec ce format:
            Classe: [PHISHING ou LEGITIME]
            Confiance: [0 à 10, où 10 est très confiant]
            Raison: [une phrase concise expliquant ta décision]
            """

        # --- CORRECTION 3: Gérer les paramètres de génération par défaut et la surcharge ---
        self.default_generation_params = settings.LLM_GENERATION_PARAMS.copy()
        if generation_config:
            self.default_generation_params.update(generation_config)

    def _parse_response(self, raw_response):
        """
        Parse la réponse textuelle brute du modèle.
        Cette fonction est restaurée à partir de la logique du POC.
        """
        result = {
            "classification": "UNKNOWN", # Renommé pour la cohérence
            "confidence_score": "UNKNOWN", # Renommé pour la cohérence
            "reason": "N/A"
        }
        if not raw_response:
            print("[LLM] Avertissement: Tentative de parser une réponse vide.")
            return result

        lines = raw_response.strip().split('\n')
        for line in lines:
            if line.lower().startswith("classe:"):
                result["classification"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("confiance:"):
                result["confidence_score"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("raison:"):
                result["reason"] = line.split(":", 1)[1].strip()
        
        if result["classification"] == "UNKNOWN" and raw_response:
             print(f"[LLM] Avertissement: Impossible de parser la 'Classe' depuis la réponse: '{raw_response}'")
        return result

    def analyze(self, email_data, generation_params_override=None):
        """
        Génère une analyse de phishing pour un e-mail donné.
        
        Args:
            email_data (dict): Un dictionnaire contenant 'sender', 'subject', et 'body'.
            generation_params_override (dict, optional): Surcharge les paramètres de génération pour cet appel.
        
        Returns:
            dict: Un dictionnaire avec la classification, le score de confiance et la raison.
        """
        if not self.model or not self.tokenizer:
            return {"error": "Le modèle LLM n'est pas disponible."}

        prompt = self.prompt_template.format(
            sender=email_data.get("sender", "N/A"),
            subject=email_data.get("subject", "N/A"),
            body=email_data.get("body", "N/A")
        )
        
        messages = [{"role": "user", "content": prompt}]
        text_for_model = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        model_inputs = self.tokenizer([text_for_model], return_tensors="pt").to(self.model.device)
        
        # --- CORRECTION 3: Gérer la surcharge des paramètres de génération ---
        current_generation_params = self.default_generation_params.copy()
        if generation_params_override:
            current_generation_params.update(generation_params_override)

        try:
            generated_ids = self.model.generate(
                **model_inputs,
                **current_generation_params
            )
            
            # --- CORRECTION 2: BUG - Isoler les nouveaux tokens générés ---
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):]
            response_text = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
            
            # --- CORRECTION 1: Utiliser la logique de parsing originale ---
            return self._parse_response(response_text)

        except Exception as e:
            return {"error": f"Erreur lors de la génération de la réponse LLM : {e}", "raw_response": ""}
        


# ---- Exemple d'utilisation ----
if __name__ == "__main__":
    # Exemple de données d'e-mail
    email_example = {
        "sender": "security@paypaI-verify.com",
        "subject": "Action requise : Vérification de votre compte PayPal",
        "body": "Votre compte a été temporairement suspendu. Cliquez ici pour vérifier..."
    }
    LLM_GENERATION_PARAMS = {
    "max_new_tokens": 100,
    "do_sample": True,
    "temperature": 0.1,
    "top_p": 0.9,
    "top_k": 50,
        }
    # Création de l'analyseur LLM
    analyzer = LLMAnalyzer( model_name="Qwen/Qwen3-0.6B", generation_config=LLM_GENERATION_PARAMS) 

    # Analyse de l'e-mail
    analysis_result = analyzer.analyze(email_example)
    print(f"Classe: {analysis_result['classification']}")
    print(f"Confiance: {analysis_result['confidence_score']}")
    print(f"Raison: {analysis_result['reason']}")