import { getDashboardData } from '../api.js';

// --- Constantes et références ---
const dashboardView = document.getElementById('dashboard-view');
const periodSelect = document.getElementById('dashboard-period-select');

// Références pour les graphiques afin de les détruire avant de les redessiner
let emailsByStatusChart = null;
let statusDistributionChart = null;

// Couleurs pour les graphiques
const CHART_COLORS = {
    legitimate: '#28a745',
    suspicious: '#ffc107',
    phishing: '#dc3545'
};

// --- Fonctions d'aide (Helpers) ---

/**
 * Formate une tendance en pourcentage avec une flèche.
 * @param {number} trend - La valeur de la tendance (ex: 0.05 pour +5%).
 * @param {string} direction - 'up', 'down', ou 'neutral'.
 * @returns {string} - Le HTML à afficher (ex: <span class="positive">▲ 5.0%</span>).
 */
function formatTrend(trend, direction) {
    if (direction === 'neutral') {
        return ''; // Pas d'affichage si la tendance est neutre
    }
    const trendClass = direction === 'up' ? 'positive' : 'negative';
    const arrow = direction === 'up' ? '▲' : '▼';
    return `<span class="stat-trend ${trendClass}">${arrow} ${(Math.abs(trend) * 100).toFixed(1)}%</span>`;
}

/**
 * Formate une date ISO en une chaîne de caractères lisible.
 * @param {string} isoString - La date au format ISO (ex: "2025-08-20T14:30:00Z").
 * @returns {string} - La date formatée (ex: "20/08/2025 16:30").
 */
function formatDate(isoString) {
    if (!isoString) return 'Date inconnue';
    return new Date(isoString).toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}


// --- Fonctions de rendu (Mise à jour du DOM) ---

function renderKPIs(kpis) {
    document.getElementById('kpi-emails-analyzed').innerHTML = `
        <div class="stat-info">
            <div class="stat-number">${kpis.emails_analyzed.value.toLocaleString()}</div>
            <div class="stat-label">Emails analysés</div>
        </div>
        ${formatTrend(kpis.emails_analyzed.trend, kpis.emails_analyzed.trend_direction)}
    `;
    document.getElementById('kpi-phishing-detected').innerHTML = `
        <div class="stat-info">
            <div class="stat-number">${kpis.phishing_detected.value.toLocaleString()}</div>
            <div class="stat-label">Phishing détecté</div>
        </div>
        ${formatTrend(kpis.phishing_detected.trend, kpis.phishing_detected.trend_direction)}
    `;
    document.getElementById('kpi-threat-rate').innerHTML = `
        <div class="stat-info">
            <div class="stat-number">${kpis.threat_rate.value.toFixed(1)}%</div>
            <div class="stat-label">Taux de menace</div>
        </div>
         ${formatTrend(kpis.threat_rate.trend, kpis.threat_rate.trend_direction)}
    `;
}


function renderCharts(chartData) {
    // --- Graphique en barres---
    const ctxBar = document.getElementById('emailsByStatusChart').getContext('2d');
    if (emailsByStatusChart) emailsByStatusChart.destroy();

    // On transforme dynamiquement les données reçues de l'API
    const barChartDatasets = chartData.daily_volume.datasets.map(dataset => {
        // Associe le nom du dataset reçu de l'API à une couleur et un libellé
        let label = dataset.name;
        let color = '';
        if (dataset.name === 'Legitimate') {
            label = 'Légitime';
            color = CHART_COLORS.legitimate;
        } else if (dataset.name === 'Suspicious') {
            label = 'Suspect';
            color = CHART_COLORS.suspicious;
        } else if (dataset.name === 'Phishing') {
            label = 'Phishing';
            color = CHART_COLORS.phishing;
        }
        return {
            label: label,
            data: dataset.data,
            backgroundColor: color
        };
    });

    emailsByStatusChart = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: chartData.daily_volume.labels,
            datasets: barChartDatasets // On utilise les données transformées ici
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true }
            }
        }
    });

    // --- Graphique en anneau ---
    const ctxDoughnut = document.getElementById('statusDistributionChart').getContext('2d');
    if (statusDistributionChart) statusDistributionChart.destroy();

    statusDistributionChart = new Chart(ctxDoughnut, {
        type: 'doughnut',
        data: {
            labels: chartData.status_distribution.labels,
            datasets: [{
                data: chartData.status_distribution.data,
                backgroundColor: [CHART_COLORS.legitimate, CHART_COLORS.suspicious, CHART_COLORS.phishing]
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function renderLatestThreats(threats) {
    const listElement = document.getElementById('latest-threats-list');
    if (threats.length === 0) {
        listElement.innerHTML = '<li class="threat-item-empty">Aucune menace détectée sur cette période.</li>';
        return;
    }
    listElement.innerHTML = threats.map(threat => `
        <li class="threat-item">
            <div class="threat-details">
                <span class="threat-status ${threat.status.toLowerCase()}">${threat.status}</span>
                <span class="threat-subject" title="${threat.subject}">${threat.subject}</span>
                <span class="threat-sender">${threat.sender_address}</span>
            </div>
            <div class="threat-meta">
                <span class="threat-date">${formatDate(threat.received_at)}</span>
                <span class="threat-score">Score: ${threat.risk_score}</span>
            </div>
        </li>
    `).join('');
}


// --- Fonctions de contrôle ---

/**
 * Met à jour toute la vue du dashboard avec de nouvelles données.
 * @param {number} period - La période en jours.
 */
async function updateDashboardView(period = 7) {
    // Affiche un état de chargement
    dashboardView.classList.add('loading');

    try {
        const data = await getDashboardData(period);
        
        // Met à jour chaque section avec les nouvelles données
        renderKPIs(data.kpis);
        renderCharts(data.charts);
        renderLatestThreats(data.activity_feeds.latest_threats);

    } catch (error) {
        // En cas d'erreur, on pourrait afficher un message dans l'UI
        console.error("Échec de la mise à jour du tableau de bord:", error);
    } finally {
        // Retire l'état de chargement
        dashboardView.classList.remove('loading');
    }
}


/**
 * Fonction d'initialisation de la vue du tableau de bord.
 * S'exécute une seule fois lorsque la vue est affichée.
 */
export function initDashboardView() {
    console.log("Dashboard view initialized");
    
    // Ajoute un écouteur d'événement sur le sélecteur de période
    periodSelect.addEventListener('change', (event) => {
        const selectedValue = event.target.value; // ex: "7d", "30d", "today"
        let periodInDays;

        // Logique améliorée pour convertir la sélection en nombre de jours
        switch (selectedValue) {
            case '30d':
                periodInDays = 30;
                break;
            case 'today':
                periodInDays = 1; // "Aujourd'hui" correspond à une période de 1 jour
                break;
            case '7d':
            default:
                periodInDays = 7;
                break;
        }
        
        console.log(`Période changée. Appel de l'API pour ${periodInDays} jour(s).`);
        updateDashboardView(periodInDays);
    });
    
    // Charge les données initiales pour la période par défaut (7 jours)
    updateDashboardView(7);
}