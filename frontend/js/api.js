
import { API_BASE_URL } from './config.js';
// js/api.js
// gére tous les appels fetch vers le backend

async function handleApiResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || `HTTP error! status: ${response.status}`;
        throw new Error(errorMessage);
    }
    return await response.json();
}

/**
 * Récupère la liste des emails depuis le backend.
 */
export async function fetchEmails() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/emails`);
        return handleApiResponse(response);
    } catch (error) {
        console.error('Network error while fetching emails:', error);
        throw new Error('Impossible de se connecter au serveur pour récupérer les emails.');
    }
}

/**
 * Demande l'analyse d'un email spécifique par son ID.
 */
export async function analyzeEmailById(emailId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze/email`, {
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

/**
 * Demande l'analyse de contexte d'une URL.
 */
export async function analyzeUrlContext(url) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/url/context`, {
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
 * Demande l'analyse prédictive d'une URL.
 */
export async function analyzeUrlPredict(url) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/url/predict`, {
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




/**
 * Récupère les données du tableau de bord depuis l'API backend.
 * @param {number} period Le nombre de jours pour la période (ex: 7, 30).
 * @returns {Promise<Object>} Les données du tableau de bord.
 */
export async function getDashboardData(period = 7) {
    // 2. Utiliser la variable importée pour construire l'URL
    const url = `${API_BASE_URL}/api/dashboard/summary?period=${period}`;
    console.log(`Fetching REAL data from: ${url}`);
    
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