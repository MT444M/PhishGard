// frontend/js/app.js

const API_BASE_URL = 'http://127.0.0.1:8000';
const POLLING_INTERVAL_MS = 30000; // Interroge toutes les 30 secondes

const appState = {
    emails: [],
    analysisCache: {},
    isPolling: false, // Un drapeau pour éviter les interrogations multiples
};

// --- FONCTIONS DE L'INTERFACE UTILISATEUR (RENDERING) ---
// ... (openModal, closeModal, createEmailItemHTML, renderEmailList, refreshSingleEmailInList, populateModalWithData, showPendingStateInModal : ces fonctions ne changent pas)
function openModal() {
    document.getElementById('emailModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('emailModal').style.display = 'none';
}

function createEmailItemHTML(email) {
    const analysis = appState.analysisCache[email.id];
    const verdict = analysis ? analysis.phishgard_verdict : 'Non analysé';
    const confidence = analysis ? analysis.confidence_score : '--%';
    
    const riskClass = { 'Phishing': 'risk-high', 'Suspicious': 'risk-medium', 'Legitime': 'risk-low' }[verdict] || '';
    const scoreClass = { 'Phishing': 'high-risk', 'Suspicious': 'medium-risk', 'Legitime': 'low-risk' }[verdict] || 'text-muted';
    
    const statusIndicator = email.isAnalyzing ? '<div class="spinner"></div>' : `<div class="risk-indicator ${riskClass}"></div>`;

    return `
        <div class="email-item" data-email-id="${email.id}">
            ${statusIndicator}
            <div class="email-info">
                <div class="email-header">
                    <div class="sender">${escapeHTML(email.sender)}</div>
                    <div class="timestamp">${email.timestamp}</div>
                </div>
                <div class="subject">${escapeHTML(email.subject)}</div>
                <div class="preview">${escapeHTML(email.preview)}</div>
            </div>
            <div class="confidence-score">
                <div class="score ${scoreClass}" id="score-${email.id}">${confidence}</div>
                <div class="score-label" id="verdict-${email.id}">${verdict.toUpperCase()}</div>
            </div>
        </div>
    `;
}

function renderEmailList() {
    const container = document.getElementById('email-list-container');
    if (!container) return;
    
    if (appState.emails.length === 0) {
        container.innerHTML = '<p class="loading-message">Chargement des emails...</p>';
        return;
    }

    container.innerHTML = appState.emails.map(createEmailItemHTML).join('');
}


function refreshSingleEmailInList(emailId) {
    const emailToUpdate = appState.emails.find(e => e.id === emailId);
    const elementToReplace = document.querySelector(`.email-item[data-email-id="${emailId}"]`);
    
    if (emailToUpdate && elementToReplace) {
        elementToReplace.outerHTML = createEmailItemHTML(emailToUpdate);
    }
}

/**
 * Calcule la position en pourcentage pour la jauge heuristique.
 * @param {number} score - Le score de l'email.
 * @returns {number} - La position en pourcentage (0-100).
 */
function calculateGaugePosition(score) {
    // On définit une plage de score "raisonnable" pour l'affichage, ex: de -60 à 60
    const minScore = -60;
    const maxScore = 60;
    
    // On s'assure que le score reste dans nos bornes pour l'affichage
    const clampedScore = Math.max(minScore, Math.min(score, maxScore));
    
    // On calcule la position en pourcentage
    const position = ((clampedScore - minScore) / (maxScore - minScore)) * 100;
    
    return position;
}

/**
 * Traduit un indicateur heuristique technique en une description claire
 * avec une pastille pour le score.
 * @param {string} flag - L'indicateur brut, ex: "DMARC_PASS_STRICT (+25)"
 * @returns {string} - Le code HTML formaté.
 */
function formatHeuristicFlag(flag) {
    const translations = {
        // --- Positifs ---
        'DMARC_PASS_STRICT': "Authentification DMARC forte",
        'DMARC_PASS_MONITOR': "Authentification DMARC présente",
        'DKIM_PASS_ALIGNED': "Signature DKIM valide et alignée",
        'SPF_PASS': "Expéditeur (SPF) autorisé",
        'OSINT_DOMAIN_ESTABLISHED': "Domaine de l'expéditeur très ancien",
        'OSINT_DOMAIN_MATURE': "Domaine de l'expéditeur établi",
        'OSINT_IP_FROM_KNOWN_PROVIDER': "IP issue d'un fournisseur de confiance",

        // --- Négatifs ---
        'DMARC_RECORD_MISSING': "Aucune protection DMARC trouvée",
        'DMARC_FAIL': "Échec de l'authentification DMARC",
        'DKIM_SIGNATURE_MISSING': "Aucune signature DKIM trouvée",
        'DKIM_FAIL': "Signature DKIM invalide",
        'DKIM_PASS_UNALIGNED': "Signature DKIM non alignée avec l'expéditeur",
        'SPF_RECORD_MISSING': "Aucune protection SPF trouvée",
        'SPF_FAIL': "Échec de la vérification SPF",
        'SPF_SOFTFAIL': "Vérification SPF faible ou suspecte",
        'FROM_RETURN_PATH_MISMATCH_WEAK_AUTH': "Incohérence des domaines d'envoi",
        'REPLY_TO_DOMAIN_MISMATCH': "L'adresse de réponse est différente de l'expéditeur",
        'OSINT_DOMAIN_VERY_RECENT': "Le domaine de l'expéditeur est très récent",
        'OSINT_DOMAIN_RECENT': "Le domaine de l'expéditeur est récent",
        'OSINT_IP_BLACKLISTED': "L'IP d'envoi est sur liste noire (mauvaise réputation)",
        'OSINT_IP_SUSPICIOUS': "L'IP d'envoi est suspecte"
    };

    // Regex pour extraire le code, les paramètres et le score
    const match = flag.match(/^([A-Z_]+)(?:\((.*?)\))?\s*\((.*?)\)$/);
    if (!match) return `<span>${flag}</span>`; // Sécurité si le format est inattendu

    const [, code, params, score] = match;
    let text = translations[code] || code; // Utilise la traduction ou le code par défaut

    // Ajoute des détails si des paramètres existent
    if (params) {
        if (params.includes('age:')) {
            const age = parseInt(params.split(':')[1]);
            if (age > 365) {
                text += ` (${Math.round(age/365)} ans)`;
            } else {
                text += ` (${age} jours)`;
            }
        } else {
             text += ` (${params.replace('domain:', '')})`;
        }
    }
    
    const scoreClass = score.includes('+') ? 'positive' : 'negative';

    return `
        <div class="heuristic-item-text">${text}</div>
        <span class="score-pill ${scoreClass}">${score}</span>
    `;
}

function showPendingStateInModal() {
    // Bannière
    const banner = document.getElementById('modal-verdict-banner');
    banner.className = 'modal-verdict-banner verdict-pending'; // Reset classes
    document.getElementById('verdict-icon').innerText = '⏳';
    document.getElementById('verdict-text').innerText = 'Analyse en cours...';
    document.getElementById('verdict-confidence').innerText = 'Veuillez patienter';

    // Cartes
    document.getElementById('heuristic-gauge-marker').style.left = '50%';
    document.getElementById('heuristic-marker-value').innerText = '--';
    document.getElementById('heuristic-details').innerHTML = '<span class="text-muted">En attente des résultats...</span>';

    // AFFICHER LA VUE D'ANALYSE PAR DÉFAUT
    document.getElementById('url-analysis-view').style.display = 'block';
    document.getElementById('url-empty-state').style.display = 'none';
    document.getElementById('url-prediction').innerText = 'En attente...'

    document.getElementById('llm-score').innerText = '--/10';
    document.getElementById('llm-reason').innerText = 'En attente de l\'analyse du contenu...';

    document.getElementById('osint-details').innerHTML = '<span class="text-muted">En attente des résultats...</span>';
}


function populateModalWithData(data) {
    // --- 1. MISE À JOUR DE LA BANNIÈRE DE VERDICT ---
    const banner = document.getElementById('modal-verdict-banner');
    const verdict = data?.phishgard_verdict ?? "Inconnu";
    let icon = '❓';
    let bannerClass = 'verdict-pending';

    switch (verdict.toLowerCase()) {
        case 'legitime':
            icon = '✅';
            bannerClass = 'verdict-legitime';
            break;
        case 'suspicious':
            icon = '⚠️';
            bannerClass = 'verdict-suspicious';
            break;
        case 'phishing':
            icon = '🚨';
            bannerClass = 'verdict-phishing';
            break;
    }
    banner.className = 'modal-verdict-banner ' + bannerClass;
    document.getElementById('verdict-icon').innerText = icon;
    document.getElementById('verdict-text').innerText = verdict;
    document.getElementById('verdict-confidence').innerText = `Niveau de confiance : ${data?.confidence_score ?? '--%'}`;

    // --- 2. CARTE HEURISTIQUE ---
    const heuristic = data?.breakdown?.heuristic_analysis;
    if (heuristic) {

        // NOUVELLE LOGIQUE POUR LA JAUGE
        const score = heuristic.score ?? 0;
        const marker = document.getElementById('heuristic-gauge-marker');
        const markerValue = document.getElementById('heuristic-marker-value');

        marker.style.left = `${calculateGaugePosition(score)}%`;
        markerValue.innerText = score;

        // On met à jour la couleur du marqueur en fonction du verdict
        if (score >= 20) {
            marker.style.backgroundColor = '#28a745'; // Vert
        } else if (score <= -20) {
            marker.style.backgroundColor = '#dc3545'; // Rouge
        } else {
            marker.style.backgroundColor = '#ffc107'; // Jaune
        }

        const detailsContainer = document.getElementById('heuristic-details');
        detailsContainer.innerHTML = ''; // Vider les anciens résultats
        
        const positiveItems = heuristic.details?.positive_indicators ?? [];
        positiveItems.forEach(item => {
            // ON UTILISE LA NOUVELLE FONCTION ICI
            detailsContainer.innerHTML += `<div class="heuristic-item positive">${formatHeuristicFlag(item)}</div>`;
        });
        
        const negativeItems = heuristic.details?.negative_indicators ?? [];
        negativeItems.forEach(item => {
            // ET LÀ AUSSI
            detailsContainer.innerHTML += `<div class="heuristic-item negative">${formatHeuristicFlag(item)}</div>`;
        });

    }

    // --- 3. CARTE ANALYSE DES LIENS ---
    const urlMl = data?.breakdown?.url_ml_analysis;
    const urlAnalysisView = document.getElementById('url-analysis-view');
    const urlEmptyStateView = document.getElementById('url-empty-state');

    // On vérifie si une analyse valide existe (on cherche une probabilité)
    if (urlMl && urlMl.probability_legitimate) {
        // Il y a une analyse, on affiche la vue correspondante
        urlAnalysisView.style.display = 'block';
        urlEmptyStateView.style.display = 'none';

        const probLegit = parseFloat(urlMl.probability_legitimate);
        document.getElementById('url-progress-bar').style.background = `linear-gradient(90deg, #dc3545 ${100 - probLegit - 10}%, #ffc107, #28a745 ${probLegit + 10}%)`;
        document.getElementById('url-prediction').innerText = `Prédiction : ${urlMl.prediction} (${urlMl.probability_legitimate})`;
    } else {
        // Pas d'analyse, on affiche la vue "vide"
        urlAnalysisView.style.display = 'none';
        urlEmptyStateView.style.display = 'flex'; // 'flex' pour activer le centrage
    }


    // --- 4. CARTE ANALYSE LLM ---
    const llm = data?.breakdown?.llm_analysis;
    if (llm) {
        document.getElementById('llm-score').innerText = `${llm.confidence_score ?? '--'}/10`;
        document.getElementById('llm-reason').innerText = llm.reason ?? 'Aucune raison fournie.';
    }

    // --- 5. CARTE RÉPUTATION DE L'EXPÉDITEUR ---
    const osint = data?.breakdown?.osint_enrichment;
    const osintContainer = document.getElementById('osint-details');
    osintContainer.innerHTML = ''; // Vider

    if (osint?.ip_analysis?.length > 0) {
        const ipInfo = osint.ip_analysis[0];
        const org = ipInfo.ipinfo?.org?.replace('AS14618 ', '') ?? 'Inconnu';
        const abuseScore = ipInfo.abuseipdb?.abuseConfidenceScore ?? 'N/A';
        const domainAge = osint.domain_analysis ? Object.values(osint.domain_analysis)[0]?.age_days : null;

        osintContainer.innerHTML += `<div class="fact-item"><span>📍</span><span class="fact-item-label">IP:</span><span class="fact-item-value">${ipInfo.ip} (${org})</span></div>`;
        osintContainer.innerHTML += `<div class="fact-item"><span>🛡️</span><span class="fact-item-label">Score d'abus:</span><span class="fact-item-value">${abuseScore}%</span></div>`;
        if(domainAge) {
             osintContainer.innerHTML += `<div class="fact-item"><span>📅</span><span class="fact-item-label">Ancienneté Domaine:</span><span class="fact-item-value">${domainAge} jours</span></div>`;
        }
    } else {
        osintContainer.innerHTML = '<span class="text-muted">Aucune donnée de réputation trouvée.</span>';
    }
    
    // --- CONTENU DE L'EMAIL (inchangé) ---
    const emailBody = data?.breakdown?.heuristic_analysis?.details?.body_preview ?? 'Le contenu de l\'email n\'est pas disponible.';
    document.getElementById('email-body-content').innerText = emailBody;

}


// --- LOGIQUE D'ANALYSE ET D'INTERACTION ---

function handleEmailClick(emailId) {
    document.querySelectorAll('.email-item').forEach(i => i.classList.remove('selected'));
    document.querySelector(`.email-item[data-email-id="${emailId}"]`)?.classList.add('selected');

    const analysisResult = appState.analysisCache[emailId];
    if (analysisResult) {
        populateModalWithData(analysisResult);
    } else {
        showPendingStateInModal();
    }
    openModal();
}

async function analyzeSingleEmail(email) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze/email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email_id: email.id }),
        });
        if (!response.ok) throw new Error(`Erreur API pour ${email.id}`);
        const analysisResult = await response.json();
        appState.analysisCache[email.id] = analysisResult;
    } catch (error) {
        console.error(`L'analyse de l'email ${email.id} a échoué:`, error);
        appState.analysisCache[email.id] = { phishgard_verdict: "Erreur d'analyse", breakdown: {} };
    } finally {
        email.isAnalyzing = false;
        refreshSingleEmailInList(email.id);
    }
}

async function startBackgroundAnalysis() {
    console.log("Lancement de l'analyse en arrière-plan...");
    // Copie de la liste pour éviter les problèmes si elle est modifiée pendant la boucle
    const emailsToAnalyze = [...appState.emails];
    for (const email of emailsToAnalyze) {
        if (!appState.analysisCache[email.id]) {
            email.isAnalyzing = true;
            refreshSingleEmailInList(email.id);
            await analyzeSingleEmail(email);
        }
    }
    console.log("Toutes les analyses en arrière-plan sont terminées.");
}


// ==========================================================
// NOUVELLE FONCTION POUR LE POLLING
// ==========================================================
async function pollForNewEmails() {
    if (appState.isPolling) return; // Empêche les appels simultanés

    console.log("Polling: Vérification de nouveaux emails...");
    appState.isPolling = true;

    try {
        const response = await fetch(`${API_BASE_URL}/api/emails`);
        if (!response.ok) throw new Error('La réponse de l\'API n\'est pas OK');
        
        const newEmailList = await response.json();
        const existingEmailIds = new Set(appState.emails.map(e => e.id));
        
        const newlyFoundEmails = newEmailList.filter(e => !existingEmailIds.has(e.id));

        if (newlyFoundEmails.length > 0) {
            console.log(`${newlyFoundEmails.length} nouvel(s) email(s) trouvé(s) !`);
            // Ajoute les nouveaux emails au début de la liste
            appState.emails.unshift(...newlyFoundEmails);
            renderEmailList(); // Met à jour toute la liste avec les nouveaux en haut
            startBackgroundAnalysis(); // Lance l'analyse pour les nouveaux
        }

    } catch (error) {
        console.error("Erreur durant le polling:", error);
    } finally {
        appState.isPolling = false; // Permet au prochain polling de se lancer
    }
}

async function initializeApp() {
    renderEmailList();
    try {
        const response = await fetch(`${API_BASE_URL}/api/emails`);
        if (!response.ok) throw new Error(`Erreur de l'API`);
        appState.emails = await response.json();
        renderEmailList();
        startBackgroundAnalysis();
        
        // --- DÉMARRAGE DU POLLING ---
        // Lance la vérification à intervalle régulier après l'initialisation.
        setInterval(pollForNewEmails, POLLING_INTERVAL_MS);

    } catch (error) {
        console.error('Impossible de charger la liste des emails:', error);
        alert('Erreur: Impossible de communiquer avec le backend.');
    }
}

function escapeHTML(str) {
    return str ? String(str).replace(/</g, "&lt;").replace(/>/g, "&gt;") : '';
}

// --- POINT D'ENTRÉE ---
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();

    const emailListContainer = document.getElementById('email-list-container');
    if(emailListContainer) {
        emailListContainer.addEventListener('click', function(event) {
            const emailItem = event.target.closest('.email-item');
            if (emailItem) {
                const emailId = emailItem.dataset.emailId;
                handleEmailClick(emailId);
            }
        });
    }

    window.onclick = function(event) {
        const modal = document.getElementById('emailModal');
        if (event.target === modal) closeModal();
    }
});