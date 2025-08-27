# database/models.py
# Ce fichier contient la définition de nos tables Email et EmailAnalysis.

import datetime
from sqlalchemy import (Column, Integer, String, DateTime, Float, Text,
                        ForeignKey, JSON) 
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    google_id = Column(String, unique=True, index=True) # ID unique fourni par Google
    
    # Tokens chiffrés ! Ne jamais les stocker en clair.
    encrypted_access_token = Column(String, nullable=True)
    encrypted_refresh_token = Column(String, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Email(Base):
    """Table pour stocker les métadonnées de l'e-mail original."""
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    # Clé étrangère pour lier cet e-mail à un utilisateur
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # La véritable unicité est maintenant la combinaison (user_id, gmail_id)
    gmail_id = Column(String, index=True, nullable=False)
    sender = Column(String, index=True)
    subject = Column(String)
    snippet = Column(Text)
    body_text = Column(Text, nullable=True)
    html_body = Column(Text, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User")
    analysis = relationship("EmailAnalysis", back_populates="email", uselist=False, cascade="all, delete-orphan")

class EmailAnalysis(Base):
    """Table pour stocker le rapport d'analyse PhishGard."""
    __tablename__ = "email_analyses"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False, unique=True)
    
    phishgard_verdict = Column(String, index=True)
    confidence_score = Column(Float)
    breakdown = Column(JSON)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())

    email = relationship("Email", back_populates="analysis")