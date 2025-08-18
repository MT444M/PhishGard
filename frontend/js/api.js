// js/api.js
// gére tous les appels fetch vers le backend

const API_BASE_URL = 'http://127.0.0.1:8000';

// python -m http.server 8080 : pour lancer le serveur local

/**
 * Récupère la liste des emails depuis le backend.
 */
export async function fetchEmails() {
    const response = await fetch(`${API_BASE_URL}/api/emails`);
    if (!response.ok) {
        throw new Error('Erreur API lors de la récupération des emails');
    }
    return await response.json();
}

/**
 * Demande l'analyse d'un email spécifique par son ID.
 */
export async function analyzeEmailById(emailId) {
    const response = await fetch(`${API_BASE_URL}/api/analyze/email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_id: emailId }),
    });
    if (!response.ok) {
        throw new Error(`Erreur API pour l'analyse de l'email ${emailId}`);
    }
    return await response.json();
}