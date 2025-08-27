// js/main.js

import { handleRouteChange } from './router.js';
import { closeModal, setupModalTabs } from './components/modal.js';
// --- NOUVEAUX IMPORTS POUR L'AUTHENTIFICATION ---
import { getCurrentUser } from './api.js';
import { handleLogout, initiateGoogleLogin } from './auth.js'; 

// ===================================================
// 1. SÉLECTION DES ÉLÉMENTS DU DOM
// On les met en haut pour un accès facile et performant.
// ===================================================
const userMenuBtn = document.getElementById('user-menu-btn');
const userEmailSpan = userMenuBtn.querySelector('span');
const userDropdownMenu = document.getElementById('user-dropdown-menu');
const modal = document.getElementById('emailModal');
const modalCloseBtn = document.getElementById('modal-close-btn');

// Tu dois ajouter ce conteneur dans ton fichier HTML
const loginButtonContainer = document.getElementById('login-btn-container');


// ===================================================
// 2. LOGIQUE D'AUTHENTIFICATION ET MISE À JOUR DE L'UI
// ===================================================

/**
 * Met à jour l'interface utilisateur en fonction de l'état de connexion.
 * Affiche le menu utilisateur ou le bouton de connexion.
 * @param {Object|null} user - L'objet utilisateur retourné par l'API ou null.
 */
function updateUIBasedOnAuthState(user) {
    if (user && user.email) {
        // --- CAS : UTILISATEUR CONNECTÉ ---
        userEmailSpan.textContent = user.email;
        userMenuBtn.style.display = 'flex'; // Affiche le menu avec l'email
        if (loginButtonContainer) loginButtonContainer.style.display = 'none'; // Cache le bouton de connexion
    } else {
        // --- CAS : UTILISATEUR NON CONNECTÉ ---
        userMenuBtn.style.display = 'none'; // Cache le menu utilisateur
        if (loginButtonContainer) loginButtonContainer.style.display = 'block'; // Affiche le bouton de connexion
    }
}


// ===================================================
// 3. GESTION DES ÉVÉNEMENTS
// ===================================================

/**
 * Configure tous les écouteurs d'événements de l'application.
 */
function setupEventListeners() {
    // --- Routeur ---
    window.addEventListener('hashchange', handleRouteChange);

    // --- Fenêtre Modale ---
    setupModalTabs();
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeModal);
    }

    // --- Menu Utilisateur et Déconnexion ---
    if (userMenuBtn && userDropdownMenu) {
        userMenuBtn.addEventListener('click', (event) => {
            event.stopPropagation(); // Empêche le clic de se propager à la fenêtre
            userDropdownMenu.classList.toggle('open');
        });

        const logoutButton = userDropdownMenu.querySelector('.logout');
        if (logoutButton) {
            logoutButton.addEventListener('click', handleLogout);
        }
    }
    
    // --- Bouton de connexion Google ---
    const googleLoginBtn = document.getElementById('google-login-btn');
    if (googleLoginBtn) {
        googleLoginBtn.addEventListener('click', initiateGoogleLogin);
    }

    // --- Écouteur global pour fermer les menus/modales ---
    window.addEventListener('click', (event) => {
        // Ferme le menu utilisateur si on clique en dehors
        if (userDropdownMenu && userDropdownMenu.classList.contains('open')) {
            if (!userMenuBtn.contains(event.target)) {
                userDropdownMenu.classList.remove('open');
            }
        }
        
        // Ferme la modale si on clique sur le fond grisé
        if (event.target === modal) {
            closeModal();
        }
    });
}


// ===================================================
// 4. POINT D'ENTRÉE DE L'APPLICATION
// ===================================================

/**
 * Fonction principale qui initialise l'application.
 */
async function initializeApp() {
    // Vérifie l'état de connexion et met à jour l'UI en conséquence
    const user = await getCurrentUser();
    updateUIBasedOnAuthState(user);

    // Configure tous les écouteurs d'événements
    setupEventListeners();
    
    // Charge la vue initiale en fonction de l'URL (ex: #/inbox)
    handleRouteChange();
}

// Lance l'application une fois que le DOM est entièrement chargé.
document.addEventListener('DOMContentLoaded', initializeApp);