import { API_BASE_URL } from './config.js';

// =============================================================================
// UTILITAIRES GÉNÉRAUX
// =============================================================================

/**
 * Gère la réponse des appels API et traite les erreurs de manière standardisée
 * @param {Response} response - La réponse fetch à traiter
 * @returns {Promise<Object>} - Les données JSON de la réponse
 * @throws {Error} - En cas d'erreur HTTP ou de parsing
 */
async function handleApiResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || `HTTP error! status: ${response.status}`;
        throw new Error(errorMessage);
    }
    return await response.json();
}


// =============================================================================
// GESTION DE SESSION - AUTHENTIFICATION ET UTILISATEUR
// =============================================================================

/**
 * Récupère les informations de l'utilisateur actuellement connecté
 * Le cookie de session est envoyé automatiquement par le navigateur
 * @returns {Promise<Object|null>} - Les données de l'utilisateur ou null si non connecté
 */
export async function getCurrentUser() {
    try {
        const response = await fetch(`${API_BASE_URL}/users/me`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
        });

        if (response.ok) {
            return await response.json(); // ex: { "email": "user@example.com", "google_id": "..." }
        }
        return null; // Si la réponse est 401 Unauthorized ou autre erreur
    } catch (error) {
        console.error("Erreur lors de la récupération de l'utilisateur:", error);
        return null;
    }
}

/**
 * Déconnecte l'utilisateur en appelant l'endpoint de logout du backend
 * @returns {Promise<boolean>} - True en cas de succès, false sinon
 */
export async function logoutUser() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
        });
        return response.ok;
    } catch (error) {
        console.error("Erreur lors de la déconnexion:", error);
        return false;
    }
}


// =============================================================================
// GESTION DES EMAILS - RÉCUPÉRATION
// =============================================================================

/**
 * Récupère la liste complète des emails depuis le backend
 * @returns {Promise<Array>} - Liste des emails
 * @throws {Error} - En cas d'erreur réseau ou serveur
 */
export async function fetchEmails() {
    try {
       const response = await fetch(`${API_BASE_URL}/emails`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', 
        });
        return handleApiResponse(response);
    } catch (error) {
        console.error('Network error while fetching emails:', error);
        throw new Error('Impossible de se connecter au serveur pour récupérer les emails.');
    }
}

// =============================================================================
// ANALYSE D'EMAILS
// =============================================================================

/**
 * Demande l'analyse d'un email spécifique par son ID
 * @param {string|number} emailId - L'identifiant unique de l'email à analyser
 * @returns {Promise<Object>} - Résultat de l'analyse de l'email
 * @throws {Error} - En cas d'erreur réseau ou serveur
 */
export async function analyzeEmailById(emailId) {
    try {
        const response = await fetch(`${API_BASE_URL}/analyze/email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email_id: emailId }),
        });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Network error while analyzing email ${emailId}:`, error);
        throw new Error(`Impossible de se connecter au serveur pour analyser l'email.`);
    }
}

// =============================================================================
// ANALYSE À LA DEMANDE - URLs ET CONTEXTE
// =============================================================================

/**
 * Demande l'analyse de contexte d'une URL (informations générales)
 * @param {string} url - L'URL à analyser pour le contexte
 * @returns {Promise<Object>} - Contexte et informations sur l'URL
 * @throws {Error} - En cas d'erreur réseau ou serveur
 */
export async function analyzeUrlContext(url) {
    try {
        const response = await fetch(`${API_BASE_URL}/url/context`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url }),
        });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Network error while analyzing url context for ${url}:`, error);
        throw new Error(`Impossible de se connecter au serveur pour analyser le contexte de l'URL.`);
    }
}

/**
 * Demande l'analyse prédictive d'une URL (détection de menaces)
 * @param {string} url - L'URL à analyser pour la prédiction
 * @returns {Promise<Object>} - Prédictions et score de dangerosité de l'URL
 * @throws {Error} - En cas d'erreur réseau ou serveur
 */
export async function analyzeUrlPredict(url) {
    try {
        const response = await fetch(`${API_BASE_URL}/url/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url }),
        });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Network error while analyzing url prediction for ${url}:`, error);
        throw new Error(`Impossible de se connecter au serveur pour analyser la prédiction de l'URL.`);
    }
}

// =============================================================================
// TABLEAU DE BORD - DONNÉES ET STATISTIQUES
// =============================================================================

/**
 * Récupère les données du tableau de bord pour une période donnée
 * @param {number} period - Le nombre de jours pour la période (ex: 7, 30)
 * @returns {Promise<Object>} - Les données du tableau de bord avec statistiques
 * @throws {Error} - En cas d'erreur réseau ou serveur
 */
export async function getDashboardData(period = '7d') {
    const url = `${API_BASE_URL}/dashboard/summary?period=${period}`;
    console.log(`Fetching dashboard data from: ${url}`);
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `Erreur HTTP ${response.status}` }));
            throw new Error(errorData.detail);
        }
        
        return await response.json();

    } catch (error) {
        console.error("Erreur lors de la récupération des données du tableau de bord:", error);
        throw error;
    }
}

/**
 * Récupère les données du dashboard pour une plage de dates spécifique
 * @param {string} startDate - Date de début au format YYYY-MM-DD
 * @param {string} endDate - Date de fin au format YYYY-MM-DD
 * @returns {Promise<Object>} - Les données du tableau de bord pour la période
 * @throws {Error} - En cas d'erreur réseau ou serveur
 */
export async function getDashboardDataByDateRange(startDate, endDate) {
    const url = `${API_BASE_URL}/dashboard/summary?start_date=${startDate}&end_date=${endDate}`;
    console.log(`Fetching dashboard data by date range from: ${url}`);
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `Erreur HTTP ${response.status}` }));
            throw new Error(errorData.detail);
        }
        
        return await response.json();

    } catch (error) {
        console.error("Erreur lors de la récupération des données du tableau de bord par plage de dates:", error);
        throw error;
    }
}

