# dashboard/schemas.py

from pydantic import BaseModel, Field
from typing import List
from enum import Enum
import datetime

# --- Éléments de base et réutilisables ---

class TrendDirection(str, Enum):
    """Énumération pour la direction des tendances."""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"

class KpiValue(BaseModel):
    """Structure pour un indicateur de performance clé (KPI)."""
    value: float = Field(..., description="La valeur numérique du KPI.")
    trend: float = Field(..., description="La variation en pourcentage par rapport à la période précédente.")
    trend_direction: TrendDirection = Field(..., description="La direction de la tendance.")

class Dataset(BaseModel):
    """Un ensemble de données pour un graphique, par exemple 'Phishing' ou 'Légitime'."""
    name: str = Field(..., description="Le nom de la série de données.")
    data: List[float] = Field(..., description="La liste des points de données.")

class ThreatItem(BaseModel):
    """Représente une menace unique dans le flux d'activité."""
    id: str = Field(..., description="L'ID de l'email.")
    status: str = Field(..., description="Le statut de la menace (Phishing, Suspicious).")
    risk_score: int = Field(..., description="Le score de risque calculé (0-100).")
    subject: str = Field(..., description="Le sujet de l'email.")
    sender_address: str = Field(..., description="L'adresse de l'expéditeur.")
    received_at: datetime.datetime = Field(..., description="La date de réception.")

# --- Structures principales pour chaque section ---

class RequestInfo(BaseModel):
    period: str = Field(..., description="La période demandée (ex: '7d').")
    start_date: datetime.datetime
    end_date: datetime.datetime

class Kpis(BaseModel):
    """Conteneur pour tous les KPIs."""
    emails_analyzed: KpiValue
    phishing_detected: KpiValue
    suspicious_detected: KpiValue
    threat_rate: KpiValue

class DailyVolumeChart(BaseModel):
    """Données pour le graphique de volume journalier."""
    labels: List[str] = Field(..., description="Les étiquettes pour l'axe X (ex: jours de la semaine).")
    datasets: List[Dataset]

class DistributionChart(BaseModel):
    """Données pour les graphiques de distribution (anneau, camembert)."""
    labels: List[str]
    data: List[int]

class Charts(BaseModel):
    """Conteneur pour toutes les données de graphiques."""
    daily_volume: DailyVolumeChart
    status_distribution: DistributionChart
    phishing_categories: DistributionChart # Réutilise la même structure

class ActivityFeeds(BaseModel):
    """Conteneur pour les flux d'activité."""
    latest_threats: List[ThreatItem]

# --- Modèle final de la réponse API ---

class DashboardResponse(BaseModel):
    """
    Le schéma complet pour la réponse de l'endpoint du dashboard.
    """
    request_info: RequestInfo
    kpis: Kpis
    charts: Charts
    activity_feeds: ActivityFeeds