// js/main.js

import { handleRouteChange } from './router.js';
import { closeModal, setupModalTabs } from './components/modal.js';

document.addEventListener('DOMContentLoaded', () => {
    // L'écouteur pour le routeur ne change pas
    window.addEventListener('hashchange', handleRouteChange);
    
    // La configuration des onglets ne change pas
    setupModalTabs();

    // ===================================================
    // NOUVELLE LOGIQUE UNIFIÉE POUR LES CLICS
    // ===================================================
    const userMenuBtn = document.getElementById('user-menu-btn');
    const userDropdownMenu = document.getElementById('user-dropdown-menu');
    const modal = document.getElementById('emailModal');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    // Écouteur pour ouvrir/fermer le menu utilisateur
    if (userMenuBtn && userDropdownMenu) {
        userMenuBtn.addEventListener('click', (event) => {
            // Empêche le clic de se propager à la fenêtre, ce qui fermerait le menu immédiatement
            event.stopPropagation(); 
            userDropdownMenu.classList.toggle('open');
        });
    }

    // Écouteur global sur la fenêtre pour fermer les éléments
    window.addEventListener('click', (event) => {
        // 1. Gère la fermeture du menu utilisateur
        if (userDropdownMenu && userDropdownMenu.classList.contains('open')) {
            // On vérifie que le clic n'est PAS sur le bouton du menu
            if (!userMenuBtn.contains(event.target)) {
                userDropdownMenu.classList.remove('open');
            }
        }
        
        // 2. Gère la fermeture de la modale
        if (event.target === modal) {
            closeModal();
        }
    });

    if(modalCloseBtn) {
        modalCloseBtn.addEventListener('click', () => closeModal());
    }

    // Charge la vue initiale
    handleRouteChange();
});
