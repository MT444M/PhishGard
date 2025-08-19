// js/router.js

import { loadInboxView } from './views/inbox.js';
import { loadUrlAnalyzerView } from './views/analyzer_on_demand.js'; 

const routes = {
    '#/inbox': loadInboxView,
    '#/analyzer': loadUrlAnalyzerView, // On utilise le nom de fonction corrigé
};

export function handleRouteChange() {
    const path = window.location.hash || '#/inbox';
    const loadView = routes[path] || routes['#/inbox'];
    
    document.querySelectorAll('.main-nav .nav-item').forEach(item => {
        item.classList.toggle('active', item.getAttribute('href') === path);
    });

    loadView();
}