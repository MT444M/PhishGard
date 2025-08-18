// js/views/url_analyzer.js
// Pour l'instant, ce fichier affichera simplement un message de construction
export function loadUrlAnalyzerView() {
    const appView = document.getElementById('app-view');
    appView.innerHTML = '<h1>Analyse à la demande</h1><p>Ce module est en cours de construction.</p>';
    
    // Cache la barre de filtres contextuelle
    document.getElementById('contextual-sidebar').style.display = 'none';
}