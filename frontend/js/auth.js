// /js/auth.js

import { logoutUser } from './api.js';

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