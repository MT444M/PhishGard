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


function populateModalWithData(data) {
    try {
        const verdict = data?.phishgard_verdict ?? "Inconnu";
        const confidence = data?.confidence_score ?? "0%";
        document.getElementById('modal-title').innerText = `🚨 Analyse - Verdict : ${verdict} (${confidence})`;

        const heuristic = data?.breakdown?.heuristic_analysis;
        if (heuristic && heuristic.details) {
            document.getElementById('score-heuristic').innerText = `${heuristic.score ?? '--'}/100`;
            const posIndicators = heuristic.details.positive_indicators?.join(', ') || 'Aucun';
            const negIndicators = heuristic.details.negative_indicators?.join(', ') || 'Aucun';
            document.getElementById('reason-heuristic').innerHTML = `<strong>Indicateurs Positifs:</strong> ${posIndicators}<br><strong>Indicateurs Négatifs:</strong> ${negIndicators}`;
        } else {
            document.getElementById('score-heuristic').innerText = 'N/A';
            document.getElementById('reason-heuristic').innerText = 'Données d\'analyse heuristique non disponibles.';
        }

        const url_ml = data?.breakdown?.url_ml_analysis;
        if (url_ml && url_ml.prediction && url_ml.prediction !== 'N/A') {
            const prob = url_ml.prediction === 'legitimate' ? url_ml.probability_legitimate : url_ml.probability_phishing;
            document.getElementById('score-url').innerText = prob ?? '--%';
            document.getElementById('reason-url').innerText = `Le modèle prédit que le lien est ${url_ml.prediction}.`;
        } else {
            document.getElementById('score-url').innerText = 'N/A';
            document.getElementById('reason-url').innerText = url_ml?.details ?? 'Aucune URL à analyser ou analyse non effectuée.';
        }
        
        const llm = data?.breakdown?.llm_analysis;
        if (llm && llm.classification) {
            document.getElementById('score-llm').innerText = `${llm.confidence_score ?? '--'}/10`;
            document.getElementById('reason-llm').innerText = `Raison : ${llm.reason ?? 'Non fournie.'}`;
        } else {
            document.getElementById('score-llm').innerText = 'N/A';
            document.getElementById('reason-llm').innerText = 'Données d\'analyse LLM non disponibles.';
        }

        const osint = data?.breakdown?.osint_enrichment;
        if (osint?.ip_analysis?.length > 0) {
            const ipInfo = osint.ip_analysis[0];
            const org = ipInfo?.ipinfo?.org ?? 'Inconnue';
            const abuseScore = ipInfo?.abuseipdb?.abuseConfidenceScore ?? 'N/A';
            document.getElementById('reason-osint').innerHTML = `IP: ${ipInfo.ip} (${org})<br>Score de réputation: ${abuseScore}%`;
        } else {
            document.getElementById('reason-osint').innerText = 'Données OSINT non disponibles.';
        }
        
        const fromAddress = heuristic?.details?.from_address?.address ?? 'Inconnu';
        const subject = heuristic?.details?.subject ?? 'Inconnu';
        document.getElementById('email-body-content').innerText = `De: ${fromAddress}\nSujet: ${subject}\n\n(Le corps complet de l'email serait affiché ici)`;

    } catch (error) {
        console.error("Erreur critique lors de l'affichage de la modale:", error);
        alert("Une erreur inattendue est survenue lors de la construction des détails. Veuillez vérifier la console.");
    }
}

function showPendingStateInModal() {
    document.getElementById('modal-title').innerText = 'Analyse en cours ou en attente...';
    ['heuristic', 'url', 'llm', 'osint'].forEach(type => {
        const reasonEl = document.getElementById(`reason-${type}`);
        const scoreEl = document.getElementById(`score-${type}`);
        if(reasonEl) reasonEl.innerText = 'En attente des résultats...';
        if(scoreEl) scoreEl.innerText = '--%';
    });
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