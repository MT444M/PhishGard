// js/router.js

import { loadInboxView } from './views/inbox.js';
import { loadUrlAnalyzerView } from './views/analyzer_on_demand.js'; 

// On enrichit la configuration des routes
const routes = {
    '#/inbox':    { viewId: 'inbox-view',    load: loadInboxView,    showSidebar: true },
    '#/analyzer': { viewId: 'analyzer-view', load: loadUrlAnalyzerView, showSidebar: false },
    // Ajoutez ici vos autres routes (dashboard, news, etc.)
};

export function handleRouteChange() {
    const path = window.location.hash || '#/inbox';
    const route = routes[path] || routes['#/inbox'];
    const appView = document.getElementById('app-view');

    if (!appView) return;

    // 1. On cache tous les conteneurs de vue existants
    appView.querySelectorAll('.view-container').forEach(container => {
        container.style.display = 'none';
    });

    // 2. On gère la barre latérale contextuelle
    const sidebar = document.getElementById('contextual-sidebar');
    if(sidebar) {
        sidebar.style.display = route.showSidebar ? 'block' : 'none';
    }

    // 3. On cherche le conteneur de la vue actuelle, ou on le crée s'il n'existe pas
    let viewContainer = document.getElementById(route.viewId);
    if (!viewContainer) {
        viewContainer = document.createElement('div');
        viewContainer.id = route.viewId;
        viewContainer.classList.add('view-container');
        appView.appendChild(viewContainer);
    }

    // 4. On affiche le conteneur de la vue actuelle
    viewContainer.style.display = 'block';

    // 5. On charge le contenu de la vue (la fonction vérifiera si c'est la première fois)
    route.load(viewContainer);

    // 6. On met à jour le lien actif dans la navigation principale
    document.querySelectorAll('.main-nav .nav-item').forEach(item => {
        item.classList.toggle('active', item.getAttribute('href') === path);
    });
}