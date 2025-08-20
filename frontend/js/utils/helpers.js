// js/utils/helpers.js
// contient les petites fonctions génériques.

const HEURISTIC_TRANSLATIONS = {
    'DMARC_PASS_STRICT': "Authentification DMARC forte", 'DMARC_PASS_MONITOR': "Authentification DMARC présente", 'DKIM_PASS_ALIGNED': "Signature DKIM valide et alignée", 'SPF_PASS': "Expéditeur (SPF) autorisé", 'OSINT_DOMAIN_ESTABLISHED': "Domaine de l'expéditeur très ancien", 'OSINT_DOMAIN_MATURE': "Domaine de l'expéditeur établi", 'OSINT_IP_FROM_KNOWN_PROVIDER': "IP issue d'un fournisseur de confiance", 'DMARC_RECORD_MISSING': "Aucune protection DMARC trouvée", 'DMARC_FAIL': "Échec de l'authentification DMARC", 'DKIM_SIGNATURE_MISSING': "Aucune signature DKIM trouvée", 'DKIM_FAIL': "Signature DKIM invalide", 'DKIM_PASS_UNALIGNED': "Signature DKIM non alignée avec l'expéditeur", 'SPF_RECORD_MISSING': "Aucune protection SPF trouvée", 'SPF_FAIL': "Échec de la vérification SPF", 'SPF_SOFTFAIL': "Vérification SPF faible ou suspecte", 'FROM_RETURN_PATH_MISMATCH_WEAK_AUTH': "Incohérence des domaines d'envoi", 'REPLY_TO_DOMAIN_MISMATCH': "L'adresse de réponse est différente de l'expéditeur", 'OSINT_DOMAIN_VERY_RECENT': "Le domaine de l'expéditeur est très récent", 'OSINT_DOMAIN_RECENT': "Le domaine de l'expéditeur est récent", 'OSINT_IP_BLACKLISTED': "L'IP d'envoi est sur liste noire (mauvaise réputation)", 'OSINT_IP_SUSPICIOUS': "L'IP d'envoi est suspecte"
};

const HEURISTIC_TOOLTIPS = {
    'DMARC_PASS_STRICT': "DMARC protège contre l'usurpation d'identité. Le statut 'Strict' indique la meilleure protection possible.",
    'DMARC_PASS_MONITOR': "DMARC est présent mais en mode 'surveillance', ce qui est moins sécurisé qu'un mode 'strict'.",
    'DKIM_PASS_ALIGNED': "DKIM est une signature cryptographique qui prouve que l'email n'a pas été altéré. 'Aligné' signifie que le signataire correspond à l'expéditeur.",
    'SPF_PASS': "SPF vérifie que l'email provient d'un serveur autorisé par le propriétaire du nom de domaine.",
    'OSINT_DOMAIN_ESTABLISHED': "Un nom de domaine très ancien est souvent un signe de légitimité et de confiance.",
    'DKIM_PASS_UNALIGNED': "La signature DKIM est valide, mais elle appartient à un domaine différent de celui de l'expéditeur (ex: un service d'envoi comme Mailgun ou SendGrid). C'est courant mais légèrement moins sécurisé.",
    'SPF_FAIL': "Le serveur d'envoi n'est PAS autorisé à envoyer des emails pour ce domaine. C'est un signal d'alerte important.",
    'OSINT_IP_SUSPICIOUS': "Cette adresse IP a été signalée pour des activités suspectes ou malveillantes par la communauté."
};

/**
 * Calcule la position en pourcentage pour la jauge heuristique.
 */
export function calculateGaugePosition(score) {
    const minScore = -60;
    const maxScore = 60;
    const clampedScore = Math.max(minScore, Math.min(score, maxScore));
    return ((clampedScore - minScore) / (maxScore - minScore)) * 100;
}

function getHeuristicFlagParts(flag) {
    const match = flag.match(/^([A-Z_]+)(?:\((.*?)\))?\s*\((.*?)\)$/);
    if (!match) return null;
    const [, code, params, score] = match;
    return { code, params, score };
}

function getHeuristicFlagTooltip(code) {
    const tooltipText = HEURISTIC_TOOLTIPS[code];
    return tooltipText 
        ? `<span class="tooltip-trigger">(?)<span class="tooltip-text">${tooltipText}</span></span>` 
        : '';
}

/**
 * Traduit un indicateur heuristique technique en une description claire.
 */
export function formatHeuristicFlag(flag) {
    const parts = getHeuristicFlagParts(flag);
    if (!parts) return `<span>${flag}</span>`;

    const { code, params, score } = parts;
    let text = HEURISTIC_TRANSLATIONS[code] || code;

    if (params) {
        if (params.includes('age:')) {
            const age = parseInt(params.split(':')[1]);
            text += age > 365 ? ` (${Math.round(age/365)} ans)` : ` (${age} jours)`;
        } else {
             text += ` (${params.replace('domain:', '')})`;
        }
    }

    const tooltipHTML = getHeuristicFlagTooltip(code);
    const scoreClass = score.includes('+') ? 'positive' : 'negative';

    return `
        <div class="heuristic-item-text">${text} ${tooltipHTML}</div>
        <span class="score-pill ${scoreClass}">${score}</span>
    `;
}

/**
 * Échappe les caractères HTML potentiellement dangereux.
 */
export function escapeHTML(str) {
    return str ? String(str).replace(/</g, "&lt;").replace(/>/g, "&gt;") : '';
}
