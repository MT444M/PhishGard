// js/components/modal.js

import { formatHeuristicFlag, escapeHTML } from '../utils/helpers.js';

// Petites fonctions utilitaires de normalisation
function coerceArray(maybeArrayOrObject) {
    if (Array.isArray(maybeArrayOrObject)) return maybeArrayOrObject;
    if (maybeArrayOrObject && typeof maybeArrayOrObject === 'object') {
        return Object.values(maybeArrayOrObject);
    }
    return [];
}

function normalizeUrlDetails(urlMl) {
    if (!urlMl) return [];
    // Essaye plusieurs conventions possibles
    if (Array.isArray(urlMl)) return urlMl;
    if (Array.isArray(urlMl.details)) return urlMl.details;
    if (urlMl.details) return coerceArray(urlMl.details);
    if (Array.isArray(urlMl.urls)) return urlMl.urls;
    if (urlMl.urls) return coerceArray(urlMl.urls);
    if (Array.isArray(urlMl.links)) return urlMl.links;
    if (urlMl.links) return coerceArray(urlMl.links);
    return [];
}

// Heuristique pour réparer le texte "mojibaké" (UTF‑8 lu en ISO‑8859‑1/Windows‑1252)
function looksLikeMojibake(text) {
    if (!text) return false;
    return /Ã.|Â.|â.|â|Ã¢|Ð|Ñ|ð|þ/.test(text);
}
function repairUtf8Mojibake(text) {
    try {
        const bytes = new Uint8Array(Array.from(text, ch => ch.charCodeAt(0) & 0xFF));
        const decoded = new TextDecoder('utf-8', { fatal: false }).decode(bytes);
        return decoded;
    } catch (e) {
        return text;
    }
}

// --- Fonctions de gestion de la modale (ouverture/fermeture/onglets) ---
const modalElement = document.getElementById('emailModal');
export function openModal() { if (modalElement) modalElement.style.display = 'flex'; }
export function closeModal() { if (modalElement) modalElement.style.display = 'none'; }


/**
 * Gère la logique des clics sur les onglets de la modale.
 */
export function setupModalTabs() {
    const tabsContainer = document.querySelector('.modal-tabs');
    if (!tabsContainer) return;

    tabsContainer.addEventListener('click', (event) => {
        const targetButton = event.target.closest('.modal-tab-button');
        if (!targetButton) return;

        const tabId = targetButton.dataset.tab;

        // Met à jour les boutons d'onglets
        document.querySelectorAll('.modal-tab-button').forEach(btn => {
            btn.classList.toggle('active', btn === targetButton);
        });

        // Met à jour les panneaux de contenu
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === tabId);
        });
    });
}



/**
 * Affiche un état de chargement dans la modale.
 * Cette fonction est adaptée à la NOUVELLE structure de la modale.
 */
export function showPendingStateInModal() {
    // 1. Mettre à jour la bannière principale
    const banner = document.getElementById('modal-verdict-banner');
    if (banner) {
        banner.className = 'modal-verdict-banner verdict-pending';
        banner.innerHTML = `
            <span class="verdict-icon">⏳</span>
            <div>
                <div class="verdict-text">Analyse en cours...</div>
                <div class="verdict-confidence">Veuillez patienter</div>
            </div>
            <span class="close" onclick="closeModal()" title="Fermer">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </span>`;
    }

    // 2. Mettre à jour l'onglet Synthèse
    const summaryScore = document.getElementById('summary-verdict-score');
    const summaryText = document.getElementById('summary-verdict-text');
    const summaryFactors = document.getElementById('summary-factors-list');
    const summaryAI = document.getElementById('summary-ai-text');
    
    if (summaryScore) summaryScore.innerText = '...';
    if (summaryText) summaryText.innerText = 'Analyse en cours';
    if (summaryFactors) summaryFactors.innerHTML = `<li>Analyse en cours...</li>`;
    if (summaryAI) summaryAI.innerText = '...';

    // 3. Mettre à jour l'onglet Analyse Détaillée (vider les sections)
    const loadingMessage = '<p style="padding: 1rem; color: var(--text-secondary);">Chargement des données...</p>';
    const detailsOrigin = document.getElementById('details-origin-content');
    const detailsPath = document.getElementById('details-path-content');
    const detailsContent = document.getElementById('details-content-content');
    const detailsTech = document.getElementById('details-tech-content');

    if (detailsOrigin) detailsOrigin.innerHTML = loadingMessage;
    if (detailsPath) detailsPath.innerHTML = loadingMessage;
    if (detailsContent) detailsContent.innerHTML = loadingMessage;
    if (detailsTech) detailsTech.innerHTML = loadingMessage;

    // 4. Mettre à jour la prévisualisation de l'email
   const previewContentArea = document.querySelector('#email-preview-container .email-preview-content');
    if (previewContentArea) {
        previewContentArea.innerHTML = `<p style="text-align: center; padding: 2rem; color: var(--text-secondary);">Chargement du contenu de l'email...</p>`;
    }
}


// --- Fonctions de remplissage du contenu ---

/**
 * Point d'entrée principal pour remplir la modale avec les données.
 * @param {object} analysisData - Le rapport d'analyse complet.
 * @param {object} emailObject - L'objet e-mail original.
 */
export function populateModalWithData(analysisData, emailObject) {
    try { populateVerdictBanner(analysisData); } catch (e) { console.error('Erreur populateVerdictBanner:', e); }
    try { populateSummaryTab(analysisData); } catch (e) { console.error('Erreur populateSummaryTab:', e); }
    try { populateDetailsTab(analysisData); } catch (e) { console.error('Erreur populateDetailsTab:', e); }
    try { populateEmailPreview(emailObject, analysisData); } catch (e) { console.error('Erreur populateEmailPreview:', e); }
}

/**
 * Remplit la bannière de verdict en haut de la modale.
 */
function populateVerdictBanner(data) {
    const banner = document.getElementById('modal-verdict-banner');
    if (!banner) return;

    const verdict = data?.phishgard_verdict ?? "Indéterminé";
    const confidence = data?.confidence_score ?? '--%';
    
    let icon = '❓';
    let bannerClass = 'verdict-pending';
    switch (verdict.toLowerCase()) {
        case 'legitime': icon = '✅'; bannerClass = 'verdict-legitime'; break;
        case 'suspicious': icon = '⚠️'; bannerClass = 'verdict-suspicious'; break;
        case 'phishing': icon = '🚨'; bannerClass = 'verdict-phishing'; break;
    }

    banner.className = `modal-verdict-banner ${bannerClass}`;
    banner.innerHTML = `
        <span class="verdict-icon">${icon}</span>
        <div>
            <div class="verdict-text">${verdict}</div>
            <div class="verdict-confidence">Niveau de confiance : ${confidence}</div>
        </div>
        <span class="close" onclick="closeModal()" title="Fermer">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </span>`;
}



// js/components/modal.js

/**
 * Remplit l\'onglet "Synthèse".
 * VERSION ENTIÈREMENT REVUE AVEC CARTE ET ANNEAU DE SCORE
 */
function populateSummaryTab(data) {
    const tabContent = document.getElementById('tab-summary');
    const verdictBlock = tabContent.querySelector('.summary-verdict-block');
    const factorsList = document.getElementById('summary-factors-list');

    // 1. Préparation des données pour l\'affichage
    const verdict = data.phishgard_verdict || 'Indéterminé';
    const score = parseFloat(data.final_score_internal ?? 0);
    const absScore = Math.abs(score);
    const verdictClass = `verdict-${verdict.toLowerCase().replace(' ', '-')}`;

    // On convertit le score (supposé sur une échelle de 100) en degrés (0-360)
    // On s\'assure que le score visuel ne dépasse pas 100 pour l\'anneau.
    const scoreForRing = Math.min(absScore, 100);
    const scoreDegrees = (scoreForRing / 100) * 360;

    // 2. Réinitialisation et stylisation de la carte de verdict
    verdictBlock.innerHTML = ''; // On vide la carte
    verdictBlock.className = 'summary-verdict-block'; // On réinitialise ses classes
    verdictBlock.classList.add(verdictClass); // On ajoute la classe pour la couleur de l\'anneau

    // 3. Création et assemblage de la nouvelle structure HTML
    const ringEl = document.createElement('div');
    ringEl.className = 'score-ring';
    // On passe le nombre de degrés à la variable CSS --score-deg
    ringEl.style.setProperty('--score-deg', `${scoreDegrees}deg`);

    const scoreEl = document.createElement('div');
    scoreEl.className = 'summary-score';
    // On formate le score avec la valeur absolue et le symbole "%"
    scoreEl.innerText = `${absScore.toFixed(1)}%`;

    const textEl = document.createElement('div');
    textEl.className = 'summary-text';
    textEl.innerText = verdict;

    // On ajoute le score dans l\'anneau
    ringEl.appendChild(scoreEl);
    // On ajoute l\'anneau et le verdict à la carte
    verdictBlock.appendChild(ringEl);
    verdictBlock.appendChild(textEl);

    // On ajoute le sous-titre si l\'information existe
    if (data.summary) {
        const subtitleEl = document.createElement('p');
        subtitleEl.className = 'summary-subtitle';
        subtitleEl.innerText = data.summary;
        verdictBlock.appendChild(subtitleEl);
    }

    // 4. Remplissage des cartes restantes (logique inchangée)
    // Cartes des méthodes
    const oldGrid = tabContent.querySelector('.summary-methods-grid');
    if (oldGrid) {
        oldGrid.remove();
    }
    const gridContainer = document.createElement('div');
    gridContainer.className = 'summary-methods-grid';
    gridContainer.innerHTML = generateMethodCards(data.breakdown);
    verdictBlock.after(gridContainer);

    // Facteurs clés
    if (factorsList) {
        factorsList.innerHTML = generateKeyFactors(data).join('');
    }
}

/**
 * Génère les 2-3 facteurs clés de la décision pour la synthèse.
 * @param {object} data - Le rapport d\'analyse.
 * @returns {string[]} - Une liste d\'éléments HTML <li>.
 */
function generateKeyFactors(data) {
    const factors = [];
    const breakdown = data.breakdown;

    if (!breakdown) return ['<li>Aucun facteur clé disponible.</li>'];

    // Priorité 1: Analyse du contenu
    if (breakdown.llm_analysis?.classification === 'PHISHING') {
        factors.push({ text: "Le contenu de l\'e-mail est jugé malveillant par l\'IA", type: 'high' });
    }
    
    // Priorité 2: Analyse Heuristique (points négatifs)
    if (breakdown.heuristic_analysis?.classification === 'PHISHING') {
        factors.push({ text: "Échec critique de l\'authentification de l\'expéditeur", type: 'high' });
    } else if (breakdown.heuristic_analysis?.authentication_strength === 'weak') {
        factors.push({ text: "L\'authentification de l\'expéditeur est faible", type: 'medium' });
    }

    // Priorité 3: Analyse des liens
    if (breakdown.url_ml_analysis?.prediction === 'phishing') {
        factors.push({ text: "Des liens de phishing ont été détectés", type: 'high' });
    }
    
    // Point positif pour équilibrer
    if (breakdown.heuristic_analysis?.authentication_strength === 'strong') {
        factors.push({ text: "L\'expéditeur a été authentifié avec succès", type: 'low' });
    }

    const icons = { 
        high: '<svg style="color: var(--risk-high-solid);"...></svg>', // (SVG complet omis pour la lisibilité)
        medium: '<svg style="color: var(--risk-medium-solid);"...></svg>',
        low: '<svg style="color: var(--risk-low-solid);"...></svg>'
    };

    return factors.slice(0, 3).map(factor => `
        <li class="summary-factor-item">
            ${icons[factor.type].replace('...', factor.type === 'high' ? 'alert-triangle' : (factor.type === 'medium' ? 'alert-circle' : 'check-circle'))}
            <span>${factor.text}</span>
        </li>
    `);
}


/**
 * Remplit l\'onglet "Analyse Détaillée" en appelant des sous-fonctions.
 */
function populateDetailsTab(data) {
    // data peut être 'analysisData' ou 'analysisData.breakdown'
    // On nettoie d\'abord les placeholders "Chargement..." pour éviter qu\'ils ne restent affichés
    const originEl = document.getElementById('details-origin-content');
    const contentEl = document.getElementById('details-content-content');
    const techEl = document.getElementById('details-tech-content');
    if (originEl) originEl.innerHTML = '';
    if (contentEl) contentEl.innerHTML = '';
    if (techEl) techEl.innerHTML = '';

    const breakdown = data?.breakdown || data || {};

    try {
        populateOriginSection(breakdown?.osint_enrichment || breakdown?.osint || breakdown?.enrichment);
    } catch (e) {
        if (originEl) originEl.innerHTML = '<p class="text-muted">Impossible d\'afficher l\'origine.</p>';
        console.error('Erreur populateOriginSection:', e);
    }

    try {
        populateContentSection(breakdown?.llm_analysis || breakdown?.llm, breakdown?.url_ml_analysis || breakdown?.url_analysis || breakdown?.urls);
    } catch (e) {
        if (contentEl) contentEl.innerHTML = '<p class="text-muted">Aucune analyse de contenu disponible.</p>';
        console.error('Erreur populateContentSection:', e);
    }

    try {
        populateTechSection(breakdown?.heuristic_analysis || breakdown?.heuristic || breakdown?.header_checks || breakdown?.header_analysis);
    } catch (e) {
        if (techEl) techEl.innerHTML = '<p class="text-muted">Données techniques non disponibles.</p>';
        console.error('Erreur populateTechSection:', e);
    }
}

// --- SOUS-FONCTIONS POUR L\'ONGLET DÉTAILLÉ ---

// js/components/modal.js

/**
 * Remplit la section "Origine & Réputation", incluant maintenant l\'analyse du trajet.
 * VERSION AMÉLIORÉE
 */
function populateOriginSection(osint) {
    const container = document.getElementById('details-origin-content');
    if (!container) return;

    if (!osint) {
        container.innerHTML = '<p class="text-muted">Données d\'origine non disponibles.</p>';
        return;
    }

    // --- Partie 1 : Analyse IP (inchangée) ---
    let ipHTML = '<h4>Analyse IP</h4>';
    if (osint.ip_analysis?.length > 0) {
        // ... (le code existant pour l\'IP reste ici, pas besoin de le copier)
        const ipInfo = osint.ip_analysis[0];
        const location = [ipInfo.ipinfo?.city, ipInfo.ipinfo?.country].filter(Boolean).join(', ');
        ipHTML += `
            <div class="fact-sheet">
                <div class="fact-row">
                    <span class="fact-label">Adresse IP</span>
                    <span class="fact-value">${ipInfo.ip}</span>
                </div>
                <div class="fact-row">
                    <span class="fact-label">Hostname</span>
                    <span class="fact-value">${ipInfo.ipinfo?.hostname ?? 'N/A'}</span>
                </div>
                <div class="fact-row">
                    <span class="fact-label">Localisation</span>
                    <span class="fact-value">${location || 'N/A'}</span>
                </div>
                <div class="fact-row">
                    <span class="fact-label">Fournisseur</span>
                    <span class="fact-value">${ipInfo.abuseipdb?.isp ?? 'N/A'}</span>
                </div>
                <div class="fact-row">
                    <span class="fact-label">Score d\'Abus</span>
                    <span class="fact-value">${ipInfo.abuseipdb?.abuseConfidenceScore ?? 'N/A'}%</span>
                </div>
            </div>`;
    } else {
        ipHTML += '<p class="text-muted">Aucune information IP trouvée.</p>';
    }

    // --- Partie 2 : Analyse des Domaines (inchangée) ---
    let domainHTML = '<h4>Analyse des Domaines</h4>';
    if (osint.domain_analysis && Object.keys(osint.domain_analysis).length > 0) {
        // ... (le code existant pour les domaines reste ici, pas besoin de le copier)
        domainHTML += '<div class="fact-sheet">';
        for (const [domain, details] of Object.entries(osint.domain_analysis)) {
            let readableAge = 'N/A';
            if (typeof details.age_days === 'number') {
                const ageYears = Math.floor(details.age_days / 365);
                readableAge = ageYears > 0 ? `~ ${ageYears} an(s)` : `${details.age_days} jours`;
            }
            domainHTML += `
                <div class="fact-row">
                    <span class="fact-label">${domain}</span>
                    <span class="fact-value">${readableAge}</span>
                </div>`;
        }
        domainHTML += '</div>';
    } else {
        domainHTML += '<p class="text-muted">Aucune information de domaine trouvée.</p>';
    }

    // --- NOUVEAU : Partie 3 : Analyse du Trajet ---
    let pathHTML = '<h4>Analyse du Trajet</h4>';
    const path = osint?.path_analysis;

    if (path && path.hop_countries?.length > 0) {
        const hopCount = path.hop_countries.length;
        const totalDelay = path.hop_delays_seconds.reduce((sum, current) => sum + current, 0);

        pathHTML += `
            <div class="fact-sheet">
                <div class="fact-row">
                    <span class="fact-label">Nombre de sauts (hops)</span>
                    <span class="fact-value">${hopCount}</span>
                </div>
                <div class="fact-row">
                    <span class="fact-label">Délai total de livraison</span>
                    <span class="fact-value">${totalDelay.toFixed(2)} s</span>
                </div>
            </div>`;
    } else {
        pathHTML += '<p class="text-muted">Le trajet de l\'email est direct ou les données sont indisponibles.</p>';
    }

    // On assemble les trois parties
    container.innerHTML = ipHTML + domainHTML + pathHTML;
}


/**
 * Remplit la section "Contenu & Intention" avec un affichage des URLs amélioré.
 * VERSION AMÉLIORÉE
 */
function populateContentSection(llm, urlMl) {
    const container = document.getElementById('details-content-content');
    if (!container) return;

    let llmHTML = '';
    let urlsHTML = '';

    // --- Partie 1 : Analyse du Contenu par l\'IA (inchangée) ---
    if (llm) {
        // ... (le code de cette section reste le même)
        let reasonText = escapeHTML(llm.reason ?? 'Aucune raison fournie.');
        llmHTML = `
            <div class="content-analysis-block">
                <h4>Analyse du Contenu (IA)</h4>
                <div class="llm-analysis-block">
                    <div class="llm-header">
                        <span class="score-badge">${llm.confidence_score ?? '--'}/10</span>
                        <span class="classification-badge verdict-${(llm.classification || '').toLowerCase()}">${llm.classification || 'N/A'}</span>
                    </div>
                    <blockquote class="reason-quote">${reasonText}</blockquote>
                </div>
            </div>`;
    }

    // --- MODIFICATION MAJEURE : Partie 2 : Analyse des URLs ---
    const urlDetails = normalizeUrlDetails(urlMl);
    if (urlDetails.length > 0) {
        urlsHTML = '<div class="content-analysis-block"><h4>Analyse des URLs</h4><div class="url-list">';
        
        urlDetails.forEach(item => {
            const rawVerdict = (item.verdict || item.classification || 'N/A').toString();
            const cleanVerdict = rawVerdict.replace(/[^a-zA-Z]/g, '').toLowerCase();
            const riskClass = { 'phishing': 'high-risk', 'suspicious': 'medium-risk', 'legitimate': 'low-risk' }[cleanVerdict] || '';
            const probability = urlMl.prediction === 'phishing' 
                ? (item.probability_phishing ?? item.phishing_probability ?? item.score ?? item.confidence) 
                : (item.probability_legitimate ?? item.legitimate_probability ?? item.score ?? item.confidence);
            const score = probability ? `${parseFloat(probability).toFixed(0)}%` : 'N/A';

            // --- NOUVEAU : Extraction du nom de domaine comme texte d\'ancre ---
            let anchorText = 'Lien'; // Fallback
            try {
                // On utilise l\'objet URL natif du navigateur pour parser le lien
                const urlObj = new URL(item.url || item.href || item.link || '');
                anchorText = urlObj.hostname; // ex: "email.mg.ipinfo.io"
            } catch (e) {
                // Si l\'URL est malformée, on garde une version tronquée
                const raw = (item.url || item.href || item.link || '').toString();
                anchorText = raw.length > 50 ? raw.substring(0, 50) + '...' : raw;
                if (raw) console.warn('URL malformée détectée :', raw);
            }

            // --- NOUVEAU : Construction de la nouvelle structure HTML pour l\'URL ---
            urlsHTML += `
                <div class="url-item">
                    <div class="url-text-content">
                        <div class="url-anchor-text" title="${escapeHTML(anchorText)}">${escapeHTML(anchorText)}</div>
                        <div class="url-full-snippet" title="${escapeHTML(item.url || item.href || item.link || '')}">${escapeHTML(item.url || item.href || item.link || '')}</div>
                    </div>

                    <div class="url-actions">
                         <div class="url-meta-content">
                            <span class="url-verdict ${riskClass}">${escapeHTML(rawVerdict)}</span>
                            <span class="text-muted" title="Score de confiance"><strong>${score}</strong></span>
                        </div>
                        <button class="copy-btn" data-url="${escapeHTML(item.url || item.href || item.link || '')}" title="Copier le lien complet">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        </button>
                    </div>
                </div>`;
        });
        
        urlsHTML += '</div></div>';
    }

    container.innerHTML = llmHTML + urlsHTML;
    if (!container.innerHTML) {
        container.innerHTML = '<p class="text-muted">Aucune analyse de contenu disponible.</p>';
    }

    // --- Partie 3 : Ré-attacher l\'interactivité pour le bouton "copier" (inchangée) ---
    container.querySelectorAll('.copy-btn').forEach(button => {
        // ... (le code de cette section reste le même)
        button.addEventListener('click', (event) => {
            event.stopPropagation();
            const urlToCopy = button.dataset.url;
            navigator.clipboard.writeText(urlToCopy).then(() => {
                button.innerHTML = 'Copié !';
                setTimeout(() => {
                    button.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
                }, 1500);
            });
        });
    });
}


/**
 * Remplit la section "Vérifications Techniques".
 */
function populateTechSection(heuristic) {
    const container = document.getElementById('details-tech-content');
    if (!container) return;

    if (!heuristic) {
        container.innerHTML = '<p class="text-muted">Données techniques non disponibles.</p>';
        return;
    }

    function formatAuthStrength(value) {
        const v = String(value ?? '').toLowerCase();
        const mapping = { strong: 'Forte', weak: 'Faible', medium: 'Moyenne', none: 'Aucune' };
        if (mapping[v]) return mapping[v];
        if (!v) return 'N/A';
        return v.charAt(0).toUpperCase() + v.slice(1);
    }

    const rawStrength = heuristic.details?.authentication_strength ?? 'N/A';
    const prettyStrength = formatAuthStrength(rawStrength);

    let techHTML = `
        <div class="fact-sheet">
            <div class="fact-row">
                <span class="fact-label">Force de l\'authentification</span>
                <span class="fact-value">${prettyStrength}</span>
            </div>
        </div>`;
    techHTML += '<div class="heuristic-details-list">';
    
    (heuristic.details?.positive_indicators ?? []).forEach(item => {
        techHTML += `<div class="heuristic-item positive">${formatHeuristicFlag(item)}</div>`;
    });
    (heuristic.details?.negative_indicators ?? []).forEach(item => {
        techHTML += `<div class="heuristic-item negative">${formatHeuristicFlag(item)}</div>`;
    });

    techHTML += '</div>';
    container.innerHTML = techHTML;
}




/**
 * Remplit l\'iframe de prévisualisation de l\'e-mail en forçant l\'encodage UTF-8.
 * VERSION CORRIGÉE POUR L\'ENCODAGE
 */
function populateEmailPreview(emailObject, analysisData) {
    const contentArea = document.querySelector('#email-preview-container .email-preview-content');
    if (!contentArea) {
        console.error("La zone d'aperçu de l'email (.email-preview-content) n'a pas été trouvée.");
        return;
    }

    contentArea.innerHTML = ''; // Vider l'ancien contenu
    
    const iframe = document.createElement('iframe');
    iframe.sandbox = 'allow-same-origin';
    iframe.frameBorder = '0';
    iframe.style.width = '100%';
    iframe.style.height = '100%';

    let bodyContent = '';
    let isHtml = false;

    // 1) On récupère le contenu prioritairement depuis l'objet e-mail
    if (emailObject?.html_body && emailObject.html_body.trim() !== '') {
        bodyContent = emailObject.html_body;
        isHtml = true;
    } else if (emailObject?.body && emailObject.body.trim() !== '') {
        bodyContent = emailObject.body;
    } 
    // 2) Sinon, on cherche dans les données d'analyse
    else if (analysisData?.email?.html_body && analysisData.email.html_body.trim() !== '') {
        bodyContent = analysisData.email.html_body;
        isHtml = true;
    } else if (analysisData?.email?.body && analysisData.email.body.trim() !== '') {
        bodyContent = analysisData.email.body;
    }

    // --- MODIFIÉ : Ajout de la gestion de l\'encodage UTF-8 ---
    if (bodyContent) {
        if (isHtml) {
            // Pour le contenu HTML, on s'assure que la balise meta charset est présente.
            // On la place au début pour qu'elle soit lue en premier.
            if (!/\<meta[^>]*charset/i.test(bodyContent)) {
                iframe.srcdoc = `<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>` + bodyContent + `</body></html>`;
            } else {
                iframe.srcdoc = bodyContent;
            }
        } else {
            // Pour le texte brut, on construit un petit document HTML complet
            // en forçant l\'UTF-8 et en utilisant un style qui imite le texte brut.
            const normalized = looksLikeMojibake(bodyContent) ? repairUtf8Mojibake(bodyContent) : bodyContent;
            const escapedBody = escapeHTML(normalized);
            iframe.srcdoc = `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body { 
                            font-family: monospace, sans-serif; 
                            white-space: pre-wrap; 
                            word-break: break-word; 
                            font-size: 14px;
                        }
                    </style>
                </head>
                <body>${escapedBody}</body>
                </html>
            `;
        }
    } else {
        // Dernier recours : message d'absence de contenu
        iframe.srcdoc = `<p style="font-family: sans-serif; color: #888; padding: 1rem; text-align: center;">Le contenu de l\'email n\'est pas disponible.</p>`;
    }
    
    contentArea.appendChild(iframe);
}

/**
 * Remplit les 3 cartes de méthodes d\'analyse dans l\'onglet de synthèse.
 * VERSION CORRIGÉE ET ROBUSTIFIÉE
 */
function generateMethodCards(breakdown) {
    const heuri = breakdown?.heuristic_analysis;
    const urlMl = breakdown?.url_ml_analysis;
    const llm = breakdown?.llm_analysis;

    let cardsHTML = '';

    // Carte 1: Analyse Heuristique (inchangée)
    if (heuri) {
        const verdict = (heuri.classification || 'N/A').toLowerCase();
        cardsHTML += `
            <div class="method-card">
                <div class="method-card-title">Heuristique</div>
                <div class="method-card-score">${heuri.score ?? '--'}</div> 
                <div class="method-card-verdict ${verdict}">${verdict}</div>
            </div>
        `;
    }

    // --- Carte 2: Analyse des URLs ---
    if (urlMl && urlMl.verdict && urlMl.verdict !== 'N/A') {
        const rawVerdict = urlMl.verdict.toString();
        const cleanVerdict = rawVerdict.replace(/[^a-zA-Z]/g, '').toLowerCase();
        const score = urlMl.confidence ? parseFloat(urlMl.confidence).toFixed(0) : '--';
        
        cardsHTML += `
            <div class="method-card">
                <div class="method-card-title">Analyse URLs</div>
                <div class="method-card-score">${score}<span class="unit">%</span></div>
                <div class="method-card-verdict ${cleanVerdict}">${cleanVerdict}</div>
            </div>
        `;
    } else {
        // Cas où il n\'y a pas d\'URL à analyser
        cardsHTML += `
            <div class="method-card">
                <div class="method-card-title">Analyse URLs</div>
                <div class="method-card-score" style="opacity: 0.6;">--</div> 
                <div class="method-card-verdict" style="text-transform: none;">Aucune URL</div>
            </div>
        `;
    }

    // Carte 3: Analyse Contenu (IA) (inchangée)
    if (llm) {
        const verdict = (llm.classification || 'N/A').toLowerCase();
        cardsHTML += `
            <div class="method-card">
                <div class="method-card-title">Analyse Contenu</div>
                <div class="method-card-score">${llm.confidence_score ?? '--'}<span class="unit">/10</span></div>
                <div class="method-card-verdict ${verdict}">${verdict}</div>
            </div>
        `;
    }

    return cardsHTML;
}

//dfjbg
