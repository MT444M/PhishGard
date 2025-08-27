# database/crud.py
# Ce fichier contiendra les fonctions pour interagir avec la base de données. Nous ajoutons une fonction pour créer une analyse, 
# et une autre pour la récupérer (notre futur cache).

from sqlalchemy.orm import Session
from . import models
from datetime import datetime
import re

#--- User CRUD ---

def get_user_by_email(db: Session, email: str):
    """Récupère un utilisateur par son adresse e-mail."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_google_id(db: Session, google_id: str):
    """Récupère un utilisateur par son Google ID."""
    return db.query(models.User).filter(models.User.google_id == google_id).first()

def create_or_update_user(db: Session, email: str, google_id: str, access_token: str, refresh_token: str = None, token_expiry: datetime = None):
    """
    Crée un utilisateur s'il n'existe pas, ou met à jour ses tokens.
    IMPORTANT: Les tokens doivent être chiffrés AVANT d'appeler cette fonction.
    """
    
    user = get_user_by_google_id(db, google_id)
    
    if user:
        # Mise à jour
        user.encrypted_access_token = access_token
        if refresh_token:
            user.encrypted_refresh_token = refresh_token
        user.token_expiry = token_expiry
    else:
        # Création
        user = models.User(
            email=email,
            google_id=google_id,
            encrypted_access_token=access_token,
            encrypted_refresh_token=refresh_token,
            token_expiry=token_expiry
        )
        db.add(user)
        
    db.commit()
    db.refresh(user)
    return user

#--- Email Analysis CRUD ---

def get_analysis_by_gmail_id(db: Session, gmail_id: str, user_id: int): # <== Ajouter user_id
    """
    Récupère une analyse via l'ID Gmail, MAIS uniquement pour l'utilisateur spécifié.
    """
    return db.query(models.EmailAnalysis)\
             .join(models.Email)\
             .filter(models.Email.gmail_id == gmail_id, models.Email.user_id == user_id)\
             .first()


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


def create_email_and_analysis(db: Session, email_data: dict, analysis_report: dict, user_id: int):
    """Crée une entrée pour l'e-mail et son rapport d'analyse associé."""
    
    received_timestamp_str = email_data.get('timestamp')
    received_at_datetime = parse_date_string(received_timestamp_str)
    
    # --- BLOC DE CORRECTION POUR LA ROBUSTESSE ---
    # On s'assure qu'aucun champ textuel essentiel ne soit inséré comme None.
    # On utilise `... or ''` pour fournir une chaîne vide comme valeur par défaut.
    db_email = models.Email(
        user_id=user_id,
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