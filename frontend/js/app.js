// frontend/js/app.js

// L'URL de base de notre API backend.
const API_BASE_URL = 'http://127.0.0.1:8000';

// --- FONCTIONS DE L'INTERFACE UTILISATEUR ---

/**
 * Affiche la fenêtre modale.
 */
function openModal() {
    document.getElementById('emailModal').style.display = 'block';
}

/**
 * Ferme la fenêtre modale.
 */
function closeModal() {
    document.getElementById('emailModal').style.display = 'none';
}

/**
 * Remplit la liste des emails dans le tableau de bord principal.
 * @param {Array} emails - Une liste d'objets email provenant de l'API.
 */
function populateEmailList(emails) {
    const container = document.getElementById('email-list-container');
    container.innerHTML = ''; // Vide la liste actuelle

    emails.forEach(email => {
        const riskClass = {
            'Phishing': 'risk-high',
            'Suspicious': 'risk-medium',
            'Legitime': 'risk-low'
        }[email.verdict] || 'risk-medium';

        const scoreClass = {
            'Phishing': 'high-risk',
            'Suspicious': 'medium-risk',
            'Legitime': 'low-risk'
        }[email.verdict] || 'medium-risk';

        const emailItemHTML = `
            <div class="email-item" data-email-id="${email.id}">
                <div class="risk-indicator ${riskClass}"></div>
                <div class="email-info">
                    <div class="email-header">
                        <div class="sender">${escapeHTML(email.sender)}</div>
                        <div class="timestamp">${email.timestamp}</div>
                    </div>
                    <div class="subject">${escapeHTML(email.subject)}</div>
                    <div class="preview">${escapeHTML(email.preview)}</div>
                </div>
                <div class="confidence-score">
                    <div class="score ${scoreClass}">${email.confidence}</div>
                    <div class="score-label">${email.verdict.toUpperCase()}</div>
                </div>
            </div>
        `;
        container.innerHTML += emailItemHTML;
    });

    // Ajoute les écouteurs d'événements après avoir créé les éléments
    document.querySelectorAll('.email-item').forEach(item => {
        item.addEventListener('click', function() {
            const emailId = this.dataset.emailId;
            handleEmailClick(emailId);
            
            // Met en évidence l'élément sélectionné
            document.querySelectorAll('.email-item').forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
}

/**
 * Met à jour la fenêtre modale avec les données d'analyse détaillées.
 * @param {Object} data - Le rapport complet de l'API.
 */
function populateModalWithData(data) {
    // Titre de la modale
    document.getElementById('modal-title').innerText = `🚨 Analyse - Verdict : ${data.phishgard_verdict} (${data.confidence_score})`;
    
    // Carte Heuristique
    const heuristic = data.breakdown.heuristic_analysis;
    document.getElementById('score-heuristic').innerText = `${heuristic.score}/100`;
    document.getElementById('reason-heuristic').innerHTML = `<strong>Indicateurs Positifs:</strong> ${heuristic.details.positive_indicators.join(', ')}<br><strong>Indicateurs Négatifs:</strong> ${heuristic.details.negative_indicators.join(', ')}`;

    // Carte URL ML
    const url_ml = data.breakdown.url_ml_analysis;
    document.getElementById('score-url').innerText = url_ml.prediction === 'legitimate' ? url_ml.probability_legitimate : url_ml.probability_phishing;
    document.getElementById('reason-url').innerText = `Le modèle prédit que le lien est ${url_ml.prediction}.`;
    
    // Carte LLM
    const llm = data.breakdown.llm_analysis;
    document.getElementById('score-llm').innerText = `${llm.confidence_score}/10`;
    document.getElementById('reason-llm').innerText = `Raison : ${llm.reason}`;

    // Carte OSINT
    const osint = data.breakdown.osint_enrichment;
    const ipInfo = osint.ip_analysis[0];
    document.getElementById('reason-osint').innerHTML = `IP: ${ipInfo.ip} (${ipInfo.ipinfo.org})<br>Score de réputation: ${ipInfo.abuseipdb.abuseConfidenceScore}%`;
    
    // Contenu de l'email (pour la démo, on utilise le résumé)
    document.getElementById('email-body-content').innerText = `De: ${data.breakdown.heuristic_analysis.details.from_address.address}\nSujet: ${data.breakdown.heuristic_analysis.details.subject}\n\n(Le corps complet de l'email serait affiché ici)`;
}

function showLoadingState() {
    document.getElementById('modal-title').innerText = 'Analyse en cours...';
    ['heuristic', 'url', 'llm', 'osint'].forEach(type => {
        const reasonEl = document.getElementById(`reason-${type}`);
        if(reasonEl) reasonEl.innerText = 'Chargement...';
    });
    openModal();
}


// --- LOGIQUE D'APPEL À L'API ---

/**
 * Gère le clic sur un email : appelle l'API pour lancer l'analyse.
 * @param {string} emailId - L'ID de l'email sur lequel on a cliqué.
 */
async function handleEmailClick(emailId) {
    console.log(`Analyse demandée pour l'email ID: ${emailId}`);
    showLoadingState();

    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze/email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email_id: emailId }),
        });

        if (!response.ok) {
            throw new Error(`Erreur de l'API: ${response.statusText}`);
        }

        const analysisResult = await response.json();
        console.log('Rapport d\'analyse reçu:', analysisResult);
        populateModalWithData(analysisResult);

    } catch (error) {
        console.error('Erreur lors de l\'analyse de l\'email:', error);
        alert('Une erreur est survenue lors de l\'analyse. Vérifiez la console.');
        closeModal();
    }
}

/**
 * Charge la liste initiale des emails depuis l'API.
 */
async function loadInitialEmails() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/emails`);
        if (!response.ok) {
            throw new Error(`Erreur de l'API: ${response.statusText}`);
        }
        const emails = await response.json();
        populateEmailList(emails);
    } catch (error) {
        console.error('Impossible de charger la liste des emails:', error);
        alert('Erreur: Impossible de communiquer avec le backend. Assurez-vous que le serveur PhishGard-AI est bien démarré.');
    }
}

// Utilitaire pour éviter les injections XSS simples
function escapeHTML(str) {
    return str.replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// --- POINT D'ENTRÉE ---

// Cette fonction s'exécute lorsque le contenu de la page est entièrement chargé.
document.addEventListener('DOMContentLoaded', () => {
    loadInitialEmails();

    // Ajoute la logique pour fermer la modale en cliquant à l'extérieur
    window.onclick = function(event) {
        const modal = document.getElementById('emailModal');
        if (event.target === modal) {
            closeModal();
        }
    }
});