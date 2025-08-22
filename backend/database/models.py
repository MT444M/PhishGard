# database/models.py
# Ce fichier contient la définition de nos tables Email et EmailAnalysis.


from sqlalchemy import (Column, Integer, String, DateTime, Float, Text,
                        ForeignKey, JSON)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Email(Base):
    """Table pour stocker les métadonnées de l'e-mail original."""
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String, unique=True, index=True, nullable=False)
    sender = Column(String, index=True)
    subject = Column(String)
    snippet = Column(Text)
    body_text = Column(Text, nullable=True)
    html_body = Column(Text, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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