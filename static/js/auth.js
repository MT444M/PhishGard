// /js/auth.js

import { logoutUser } from './api.js';
import { API_BASE_URL } from './config.js';

/**
 * Fonction de connexion Google qui utilise l'URL relative API_BASE_URL au lieu d'une URL codée en dur
 * Cela permet d'avoir la même base URL que celle utilisée par le reste de l'application
 */
export function initiateGoogleLogin() {
    window.location.href = `${API_BASE_URL}/auth/login`;
}

/**
 * Gère le clic sur le bouton de déconnexion.
 * Appelle l'API de déconnexion et rafraîchit la page.
 */
export async function handleLogout(event) {
    event.preventDefault(); // Empêche le lien de suivre "#"
    
    const success = await logoutUser();
    
    if (success) {
        // La déconnexion a réussi, le cookie est supprimé par le backend.
        // On rafraîchit la page pour réinitialiser l'état du frontend.
        window.location.href = '/'; // ou window.location.reload();
    } else {
        alert("La déconnexion a échoué. Veuillez réessayer.");
    }
}