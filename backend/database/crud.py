# database/crud.py
# Ce fichier contiendra les fonctions pour interagir avec la base de données. Nous ajoutons une fonction pour créer une analyse, 
# et une autre pour la récupérer (notre futur cache).

from sqlalchemy.orm import Session
from . import models
from datetime import datetime, timezone
import re

def get_analysis_by_gmail_id(db: Session, gmail_id: str):
    """Récupère une analyse via l'ID Gmail de l'email associé."""
    return db.query(models.EmailAnalysis).join(models.Email).filter(models.Email.gmail_id == gmail_id).first()


def parse_date_string(date_str: str):
    """Analyse de manière robuste une chaîne de date pour la convertir en objet datetime."""
    if not date_str:
        return None
    
    match = re.search(r'(\w{3},\s+\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s+[+-]\d{4})', date_str)
    if not match:
        return None

    clean_date_str = match.group(1)
    
    try:
        return datetime.strptime(clean_date_str, '%a, %d %b %Y %H:%M:%S %z')
    except (ValueError, TypeError):
        return None


def create_email_and_analysis(db: Session, email_data: dict, analysis_report: dict):
    """Crée une entrée pour l'e-mail et son rapport d'analyse associé."""
    
    received_timestamp_str = email_data.get('timestamp')
    received_at_datetime = parse_date_string(received_timestamp_str)
    
    # --- BLOC DE CORRECTION POUR LA ROBUSTESSE ---
    # On s'assure qu'aucun champ textuel essentiel ne soit inséré comme None.
    # On utilise `... or ''` pour fournir une chaîne vide comme valeur par défaut.
    db_email = models.Email(
        gmail_id=email_data.get('id'), # L'ID est critique, on ne met pas de défaut.
        sender=email_data.get('sender') or "Expéditeur inconnu",
        subject=email_data.get('subject') or "Sujet non disponible",
        snippet=email_data.get('snippet') or "", 
        body_text=email_data.get('body') or "",
        html_body=email_data.get('html_body') or "",
        received_at=received_at_datetime
    )
    # -----------------------------------------------
    
    score_str = analysis_report.get('confidence_score', '0%').replace('%', '')
    try:
        score_float = float(score_str)
    except (ValueError, TypeError):
        score_float = 0.0

    db_analysis = models.EmailAnalysis(
        phishgard_verdict=analysis_report.get('phishgard_verdict'),
        confidence_score=score_float,
        breakdown=analysis_report.get('breakdown', {})
    )
    
    db_analysis.email = db_email
    
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    
    return db_email