// js/router.js
// fait le lien entre les URL et les fonctions qui chargent les vues.

import { loadInboxView } from './views/inbox.js';
import { loadUrlAnalyzerView } from './views/analyzer_on_demand.js';

// Mappe une "route" (le hash dans l'URL) à une fonction de chargement de vue
const routes = {
    '#/inbox': loadInboxView,
    '#/analyzer': loadUrlAnalyzerView,
    // On ajoutera les futures routes ici
};

// Gère le changement de route
export function handleRouteChange() {
    const path = window.location.hash || '#/inbox'; // Route par défaut
    const loadView = routes[path] || routes['#/inbox']; // Sécurité
    
    // Met à jour la classe 'active' sur le bon lien de navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.getAttribute('href') === path);
    });

    loadView();
}