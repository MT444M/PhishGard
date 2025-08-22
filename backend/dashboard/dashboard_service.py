# dashboard/dashboard_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func, case
from . import schemas
from database import models
from datetime import datetime, timedelta, timezone
import locale


# --- Fonctions utilitaires (helpers) ---

def _calculate_trend(current_value: float, previous_value: float) -> tuple[float, schemas.TrendDirection]:
    """Calcule la tendance en pourcentage et sa direction."""
    if previous_value == 0:
        trend = 1.0 if current_value > 0 else 0.0
    else:
        trend = (current_value - previous_value) / previous_value
    
    if trend > 0:
        direction = schemas.TrendDirection.UP
    elif trend < 0:
        direction = schemas.TrendDirection.DOWN
    else:
        direction = schemas.TrendDirection.NEUTRAL
        
    return round(trend, 4), direction


# --- Fonction principale du service ---

def get_dashboard_summary(db: Session, period_days: int = 7) -> schemas.DashboardResponse:
    """
    Fonction principale qui agrège toutes les métriques pour le dashboard.
    """
    # --- 0. Définition des périodes de temps et de la langue ---
    try:
        # Définit la langue pour les noms des jours (ex: 'Ven.' au lieu de 'Fri.')
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except locale.Error:
        # Fallback au cas où la locale fr_FR n'est pas installée sur le système
        print("Avertissement: Locale 'fr_FR.UTF-8' non trouvée. Les jours seront en anglais.")

    end_date = datetime.now(timezone.utc)
    today = end_date.date()

    if period_days == 7:
        # Pour la vue sur 7 jours, on commence toujours au Lundi de la semaine en cours.
        # weekday() renvoie 0 pour Lundi, ..., 6 pour Dimanche.
        start_date = (end_date - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Pour les autres vues (ex: 30 jours), on garde la période glissante.
        start_date = (end_date - timedelta(days=period_days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    # --------------------------------------------------------

    previous_start_date = start_date - timedelta(days=period_days)
    previous_end_date = start_date

    # --- 1. Calcul des KPIs et de leurs tendances ---
    current_kpis_query = db.query(
        func.count(models.EmailAnalysis.id).label("total"),
        func.sum(case((models.EmailAnalysis.phishgard_verdict == 'Phishing', 1), else_=0)).label("phishing"),
        func.sum(case((models.EmailAnalysis.phishgard_verdict == 'Suspicious', 1), else_=0)).label("suspicious")
    ).filter(models.EmailAnalysis.analyzed_at.between(start_date, end_date)).one()

    previous_kpis_query = db.query(
        func.count(models.EmailAnalysis.id).label("total"),
        func.sum(case((models.EmailAnalysis.phishgard_verdict == 'Phishing', 1), else_=0)).label("phishing"),
        func.sum(case((models.EmailAnalysis.phishgard_verdict == 'Suspicious', 1), else_=0)).label("suspicious")
    ).filter(models.EmailAnalysis.analyzed_at.between(previous_start_date, previous_end_date)).one()
    
    total_trend, total_dir = _calculate_trend(current_kpis_query.total or 0, previous_kpis_query.total or 0)
    phishing_trend, phishing_dir = _calculate_trend(current_kpis_query.phishing or 0, previous_kpis_query.phishing or 0)
    suspicious_trend, suspicious_dir = _calculate_trend(current_kpis_query.suspicious or 0, previous_kpis_query.suspicious or 0)
    current_threats = (current_kpis_query.phishing or 0) + (current_kpis_query.suspicious or 0)
    previous_threats = (previous_kpis_query.phishing or 0) + (previous_kpis_query.suspicious or 0)
    current_threat_rate = (current_threats / current_kpis_query.total * 100) if (current_kpis_query.total or 0) > 0 else 0
    previous_threat_rate = (previous_threats / previous_kpis_query.total * 100) if (previous_kpis_query.total or 0) > 0 else 0
    threat_rate_trend, threat_rate_dir = _calculate_trend(current_threat_rate, previous_threat_rate)
    
    kpis = schemas.Kpis(
        emails_analyzed=schemas.KpiValue(value=current_kpis_query.total or 0, trend=total_trend, trend_direction=total_dir),
        phishing_detected=schemas.KpiValue(value=current_kpis_query.phishing or 0, trend=phishing_trend, trend_direction=phishing_dir),
        suspicious_detected=schemas.KpiValue(value=current_kpis_query.suspicious or 0, trend=suspicious_trend, trend_direction=suspicious_dir),
        threat_rate=schemas.KpiValue(value=round(current_threat_rate, 2), trend=threat_rate_trend, trend_direction=threat_rate_dir)
    )

    # --- 2. Préparation des données pour les graphiques ---
    daily_volume_query = db.query(
        func.date(models.EmailAnalysis.analyzed_at).label("date"),
        func.sum(case((models.EmailAnalysis.phishgard_verdict == 'Phishing', 1), else_=0)).label("phishing"),
        func.sum(case((models.EmailAnalysis.phishgard_verdict == 'Suspicious', 1), else_=0)).label("suspicious"),
        func.sum(case((models.EmailAnalysis.phishgard_verdict.notin_(['Phishing', 'Suspicious']), 1), else_=0)).label("legitimate")
    ).filter(models.EmailAnalysis.analyzed_at.between(start_date, end_date)).group_by("date").order_by("date").all()
    
    data_map = {str(row.date): row for row in daily_volume_query}

    # Boucle 'while' corrigée pour générer les jours de la période
    day_labels = []
    date_keys_as_string = []
    current_day = start_date
    while current_day.date() <= end_date.date():
        # Utilise .capitalize() pour avoir la première lettre en majuscule (ex: "Ven.")
        day_labels.append(current_day.strftime('%a').capitalize())
        date_keys_as_string.append(current_day.strftime('%Y-%m-%d'))
        current_day += timedelta(days=1)

    daily_volume = schemas.DailyVolumeChart(
        labels=day_labels,
        datasets=[
            schemas.Dataset(name="Legitimate", data=[(data_map.get(key) and data_map[key].legitimate) or 0 for key in date_keys_as_string]),
            schemas.Dataset(name="Suspicious", data=[(data_map.get(key) and data_map[key].suspicious) or 0 for key in date_keys_as_string]),
            schemas.Dataset(name="Phishing", data=[(data_map.get(key) and data_map[key].phishing) or 0 for key in date_keys_as_string])
        ]
    )
    
    total_legit = (current_kpis_query.total or 0) - current_threats
    status_distribution = schemas.DistributionChart(
        labels=["Légitime", "Suspect", "Phishing"],
        data=[total_legit, current_kpis_query.suspicious or 0, current_kpis_query.phishing or 0]
    )

    phishing_categories = schemas.DistributionChart(
        labels=["Usurpation d'identité", "Malware", "Fraude", "Spam"],
        data=[45, 25, 10, 9] # Données factices
    )

    charts = schemas.Charts(
        daily_volume=daily_volume,
        status_distribution=status_distribution,
        phishing_categories=phishing_categories
    )

    # --- 3. Récupération du flux d'activité ---
    latest_threats_query = db.query(models.EmailAnalysis).join(models.Email).filter(
        models.EmailAnalysis.phishgard_verdict.in_(['Phishing', 'Suspicious'])
    ).order_by(models.EmailAnalysis.analyzed_at.desc()).limit(5).all()

    latest_threats = []
    for threat in latest_threats_query:
        item = schemas.ThreatItem(
            id=threat.email.gmail_id,
            status=threat.phishgard_verdict or "N/A",
            risk_score=int(threat.confidence_score or 0),
            subject=threat.email.subject or "Sujet non disponible",
            sender_address=threat.email.sender or "Expéditeur inconnu",
            received_at=threat.email.received_at or datetime.now(timezone.utc)
        )
        latest_threats.append(item)

    activity_feeds = schemas.ActivityFeeds(latest_threats=latest_threats)

    # --- 4. Assemblage final de la réponse ---
    import json
    from fastapi.encoders import jsonable_encoder
    response = schemas.DashboardResponse(
        request_info=schemas.RequestInfo(
            period=f"{period_days}d",
            start_date=start_date,
            end_date=end_date
        ),
        kpis=kpis,
        charts=charts,
        activity_feeds=activity_feeds
    )
    print("DASHBOARD RESPONSE JSON:", json.dumps(jsonable_encoder(response), indent=2, default=str))
    return response