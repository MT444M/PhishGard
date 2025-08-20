// js/views/inbox.js

import { escapeHTML } from '../utils/helpers.js';
import { fetchEmails, analyzeEmailById } from '../api.js';
import { openModal, populateModalWithData, showPendingStateInModal } from '../components/modal.js';

const POLLING_INTERVAL_MS = 30000;

const state = {
    emails: [],
    analysisCache: {},
    isPolling: false,
    pollingIntervalId: null
};

// --- SECTION D'ÉCOUTEURS D'ÉVÉNEMENTS ---

// On utilise un drapeau pour s'assurer que l'écouteur n'est attaché qu'une seule fois
let isInboxListenerAttached = false;

function addInboxEventListeners() {
    if (isInboxListenerAttached) return; // Si c'est déjà fait, on ne fait rien

    const appView = document.getElementById('app-view');
    if (!appView) return;

    // On attache l'écouteur au parent stable #app-view
    appView.addEventListener('click', (event) => {
        // On vérifie si le clic a eu lieu sur un item d'email
        const emailItem = event.target.closest('.email-item');
        if (emailItem) {
            handleEmailClick(emailItem.dataset.emailId);
        }
    });

    isInboxListenerAttached = true; // On lève le drapeau

    // NOUVEL ÉCOUTEUR POUR LE BOUTON DES FILTRES
    const toggleBtn = document.getElementById('toggle-filters-btn');
    const mainContentEl = document.querySelector('.main-content');

    if (toggleBtn && mainContentEl) {
        toggleBtn.addEventListener('click', () => {
            // On bascule simplement la classe sur le conteneur principal
            mainContentEl.classList.toggle('filters-visible');
        });
    }

    // NOUVELLE LOGIQUE POUR LES CARTES DE STATUT
    const filtersContainer = document.querySelector('.status-filters-grid');
    if (filtersContainer) {
        filtersContainer.addEventListener('click', (event) => {
            const selectedCard = event.target.closest('.status-card');
            if (!selectedCard) return;

            // Retire la classe 'active' de toutes les cartes
            filtersContainer.querySelectorAll('.status-card').forEach(card => {
                card.classList.remove('active');
            });

            // Ajoute la classe 'active' à la carte cliquée
            selectedCard.classList.add('active');

            const filterValue = selectedCard.dataset.filter;
            console.log(`Filtre de statut appliqué : ${filterValue}`);
            // Ici, vous ajouteriez la logique pour réellement filtrer la liste des emails
        });
    }
}


// --- SECTION DES FONCTIONS DE LA VUE ---

function createEmailItemHTML(email) {
    const analysis = state.analysisCache[email.id];
    const verdict = analysis ? analysis.phishgard_verdict : 'En cours...';
    const confidence = analysis ? parseFloat(analysis.confidence_score).toFixed(0) + '%' : '';
    const riskClass = { 'Phishing': 'risk-high', 'Suspicious': 'risk-medium', 'Legitime': 'risk-low' }[analysis?.phishgard_verdict] || '';
    const scoreClass = { 'Phishing': 'high-risk', 'Suspicious': 'medium-risk', 'Legitime': 'low-risk' }[analysis?.phishgard_verdict] || '';
    const senderName = escapeHTML(email.sender.split('<')[0].trim());
    const senderEmail = escapeHTML(email.sender.includes('<') ? email.sender.split('<')[1].replace('>', '') : email.sender);
    const initials = senderName.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase() || 'P';
    const statusIndicator = email.isAnalyzing ? '<div class="spinner"></div>' : `<div class="sender-avatar">${initials}</div>`;

    return `
        <div class="email-item ${riskClass}" data-email-id="${email.id}">
            ${statusIndicator}
            <div class="email-info">
                <div class="email-header">
                    <div class="sender-details">
                        <span class="sender">${senderName}</span>
                        <span class="sender-email">&lt;${senderEmail}&gt;</span>
                    </div>
                    <div class="timestamp">${email.timestamp}</div>
                </div>
                <div class="subject">${escapeHTML(email.subject)}</div>
                <div class="preview">${escapeHTML(email.preview)}</div>
            </div>
            ${analysis ? `<div class="email-score-pill ${scoreClass}">${confidence} ${verdict}</div>` : ''}
        </div>`;
}

function renderEmailList() {
    const container = document.getElementById('email-list-container');
    if (!container) return;
    container.innerHTML = state.emails.length > 0 ? state.emails.map(createEmailItemHTML).join('') : '<p class="loading-message">Aucun email à afficher.</p>';
}

function refreshSingleEmailInList(emailId) {
    const emailToUpdate = state.emails.find(e => e.id === emailId);
    const elementToReplace = document.querySelector(`.email-item[data-email-id="${emailId}"]`);
    if (emailToUpdate && elementToReplace) {
        elementToReplace.outerHTML = createEmailItemHTML(emailToUpdate);
    }
}

// js/views/inbox.js
async function handleEmailClick(emailId) {
    // On met en surbrillance l'email sélectionné dans la liste
    document.querySelectorAll('.email-item').forEach(i => i.classList.remove('selected'));
    const emailItem = document.querySelector(`.email-item[data-email-id="${emailId}"]`);
    if (emailItem) {
        emailItem.classList.add('selected');
    }

        // 1. On OUVRE la modale immédiatement. Elle sera vide ou en état de chargement.
    openModal();
    // 2. On affiche l'état "en attente" PENDANT que les données sont préparées.
    showPendingStateInModal();
  

    let analysisResult = state.analysisCache[emailId];
    const emailObject = state.emails.find(e => e.id === emailId);

    if (!emailObject) {
        console.error("Impossible de trouver l'objet email correspondant à l'ID:", emailId);
        // On pourrait afficher un message d'erreur dans la modale ici
        return;
    }

    // 3. Si pas d'analyse en cache, on déclenche l'analyse pour cet email et on met à jour ensuite
    if (!analysisResult) {
        try {
            await analyzeSingleEmail(emailObject);
            analysisResult = state.analysisCache[emailId];
        } catch (e) {
            console.error('Analyse à la demande échouée:', e);
        }
    }

    // 4. On REMPLIT la modale avec les données (même si partielles)
    populateModalWithData(analysisResult || {}, emailObject);
    

}

async function analyzeSingleEmail(email) {
    try {
        const analysisResult = await analyzeEmailById(email.id);
        state.analysisCache[email.id] = analysisResult;
    } catch (error) {
        console.error(`L'analyse de l'email ${email.id} a échoué:`, error);
        state.analysisCache[email.id] = { phishgard_verdict: "Erreur", confidence_score: "N/A", breakdown: {} };
    } finally {
        email.isAnalyzing = false;
        refreshSingleEmailInList(email.id);
    }
}

async function startBackgroundAnalysis() {
    const emailsToAnalyze = [...state.emails];
    for (const email of emailsToAnalyze) {
        if (!state.analysisCache[email.id]) {
            email.isAnalyzing = true;
            refreshSingleEmailInList(email.id);
            await analyzeSingleEmail(email);
        }
    }
}

async function pollForNewEmails() {
    if (state.isPolling) return;
    state.isPolling = true;
    try {
        const newEmailList = await fetchEmails();
        const existingEmailIds = new Set(state.emails.map(e => e.id));
        const newlyFoundEmails = newEmailList.filter(e => !existingEmailIds.has(e.id));
        if (newlyFoundEmails.length > 0) {
            state.emails.unshift(...newlyFoundEmails);
            renderEmailList();
            startBackgroundAnalysis();
        }
    } catch (error) {
        console.error("Erreur durant le polling:", error);
    } finally {
        state.isPolling = false;
    }
}

// La fonction principale exportée, qui charge la vue
// La fonction reçoit maintenant son propre conteneur en argument
export async function loadInboxView(viewContainer) {
    // On vérifie si le contenu a déjà été dessiné
    if (viewContainer.innerHTML.trim() !== '') {
        return; // Si oui, on ne fait rien
    }
    
    // Si c'est la première visite, on dessine le HTML
    viewContainer.innerHTML = `
        <div class="toolbar">
            <div class="search-wrapper">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <input type="text" class="search-input" placeholder="Rechercher...">
            </div>
            <div class="toolbar-actions">
            
                <button class="btn btn-secondary" id="toggle-filters-btn" title="Afficher les filtres">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21"x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>
                    <span>Filtres</span>
                </button>
                <button class="btn btn-secondary">
                    <svg ...></svg> <span>Exporter</span>
                </button>
            </div>
        </div>
        <div class="email-list" id="email-list-container"><p class="loading-message">Chargement des emails...</p></div>`;
    
    document.getElementById('contextual-sidebar').style.display = 'block';

    // On s'assure que l'écouteur global pour cette vue est bien en place
    addInboxEventListeners();

    // Le reste de la logique de chargement
    try {
        state.emails = await fetchEmails();
        renderEmailList();
        startBackgroundAnalysis();
        if (state.pollingIntervalId) clearInterval(state.pollingIntervalId);
        state.pollingIntervalId = setInterval(pollForNewEmails, POLLING_INTERVAL_MS);
    } catch (error) {
        console.error('Impossible de charger la vue Boîte de réception:', error);
        appView.innerHTML = '<p class="loading-message">Erreur: Impossible de charger les emails.</p>';
    }
}