// js/views/analyzer_on_demand.js

/**
 * Gère la logique des clics sur les onglets de la page.
 */
function setupOnDemandTabs() {
    const tabsContainer = document.querySelector('.on-demand-tabs');
    if (!tabsContainer) return;

    tabsContainer.addEventListener('click', (event) => {
        const targetButton = event.target.closest('.on-demand-tab-button');
        if (!targetButton) return;
        const tabId = targetButton.dataset.tab;

        tabsContainer.querySelectorAll('.on-demand-tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        targetButton.classList.add('active');

        document.querySelectorAll('.on-demand-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === tabId);
        });
    });
}


// js/views/analyzer_on_demand.js

/**
 * Crée le composant HTML pour le BANDEAU de résumé (Overview).
 * VERSION HORIZONTALE COMPACTE
 * @param {object} overviewData - L'objet 'overview.data' de la réponse API.
 * @returns {string} Le code HTML du composant.
 */
function createOverviewComponent(overviewData) {
    if (!overviewData) return '';

    // Fonction utilitaire pour abréger l'âge du domaine
    const formatDomainAge = (ageString) => {
        if (!ageString) return 'N/A';
        const yearMatch = ageString.match(/(\d+)\s+years?/);
        if (yearMatch && parseInt(yearMatch[1], 10) > 0) {
            return `+ ${yearMatch[1]} ans`;
        }
        const monthMatch = ageString.match(/(\d+)\s+months?/);
        if (monthMatch && parseInt(monthMatch[1], 10) > 0) {
            return `+ ${monthMatch[1]} mois`;
        }
        const dayMatch = ageString.match(/(\d+)\s+days?/);
        if (dayMatch) {
            return `${dayMatch[1]} jours`;
        }
        return ageString;
    };

    const mainIp = Array.isArray(overviewData.resolved_ip)
        ? overviewData.resolved_ip[0]
        : overviewData.resolved_ip;

    const stats = [
        {
            label: 'Domaine',
            value: overviewData.domain || 'N/A',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 0 0-7.5 16.5M22 12A10 10 0 0 0 12 2"/></svg>`
        },
        {
            label: 'IP Principale',
            value: mainIp || 'N/A',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>`
        },
        {
            label: 'Pays',
            value: overviewData.country || 'N/A',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>`
        },
        {
            label: 'Âge du Domaine',
            value: formatDomainAge(overviewData.domain_age),
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`
        },
        {
            label: 'HTTPS',
            value: overviewData.https || 'N/A',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`
        }
    ];

    const statsHTML = stats.map(stat => `
        <div class="overview-stat">
            <div class="overview-stat-icon">${stat.icon}</div>
            <div class="overview-stat-text">
                <span class="overview-stat-label">${stat.label}</span>
                <span class="overview-stat-value">${stat.value}</span>
            </div>
        </div>
    `).join('');

    return `<div class="overview-strip">${statsHTML}</div>`;
}

/**
 * NOUVELLE FONCTION
 * Gère la logique de clic pour un système d'onglets générique.
 * @param {string} containerSelector - Le sélecteur du conteneur des onglets.
 */
function setupDynamicTabs(containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    const tabsNav = container.querySelector('.details-tab-nav');
    const panesContainer = container.querySelector('.details-tab-content');

    if (!tabsNav || !panesContainer) return;

    tabsNav.addEventListener('click', (event) => {
        const targetButton = event.target.closest('.details-tab-button');
        if (!targetButton) return;

        const tabId = targetButton.dataset.tab;

        tabsNav.querySelectorAll('.details-tab-button').forEach(btn => btn.classList.remove('active'));
        targetButton.classList.add('active');

        panesContainer.querySelectorAll('.details-tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === tabId);
        });
    });
}

// js/views/analyzer_on_demand.js

/**
 * Crée le contenu HTML pour l'onglet "Domain & WHOIS".
 * VERSION COMPLÈTE ET AMÉLIORÉE
 * @param {object} whoisData - L'objet domain_whois.data de l'API.
 * @returns {string} Le code HTML du panneau.
 */
function createWhoisTabContent(whoisData) {
    if (!whoisData) {
        return '<p class="text-muted">Données WHOIS non disponibles.</p>';
    }

    // Mappe complète des clés API vers les libellés de l'interface
    const dataMap = [
        { label: 'Registrar',        key: 'Registrar' },
        { label: 'Created On',       key: 'CreationDate' },
        { label: 'Last Updated',     key: 'UpdatedDate' },
        { label: 'Expires On',       key: 'ExpirationDate' },
        { label: 'Domain Age',       key: 'DomainAge' },
        { label: 'Status',           key: 'Status' },
        { label: 'Contact Emails',   key: 'Emails' },
        { label: 'Registrant Country', key: 'Country' },
        { label: 'Name Servers',     key: 'NameServers' },
        { label: 'DNSSEC',           key: 'DNSSEC' },
        { label: 'Registrant Org',   key: 'Registrant' }
    ];

    const detailsHTML = dataMap.map(({ label, key }) => {
        let value = whoisData[key];
        
        // Formatage amélioré des valeurs
        if (value === null || value === undefined || (Array.isArray(value) && value.length === 0)) {
            value = '<span class="text-muted">Not Available</span>';
        } 
        else if (Array.isArray(value)) {
            // Gère les listes (ex: Status, NameServers) et supprime les doublons
            value = [...new Set(value)].join(', ');
        } 
        else if (key.includes('Date')) {
            // Formate les dates pour être plus lisibles en français
            try {
                value = new Date(value).toLocaleString('fr-FR', {
                    year: 'numeric', month: 'long', day: 'numeric',
                    hour: '2-digit', minute: '2-digit', second: '2-digit'
                });
            } catch (e) { /* Garde la valeur originale si la date est invalide */ }
        }

        return `
            <div class="detail-item">
                <span class="detail-label">${label}</span>
                <span class="detail-value">${value}</span>
            </div>
        `;
    }).join('');

    return `
        <div class="details-section">
            <h4 class="details-section-title">Registration Details</h4>
            ${detailsHTML}
        </div>
    `;
}


// js/views/analyzer_on_demand.js

/**
 * NOUVELLE FONCTION
 * Crée le contenu HTML pour l'onglet "DNS".
 * @param {object} dnsData - L'objet dns.data de l'API.
 * @returns {string} Le code HTML du panneau.
 */
function createDnsTabContent(dnsData) {
    if (!dnsData || !dnsData.A_records || dnsData.A_records.length === 0) {
        return '<p class="text-muted">Aucun enregistrement DNS de type A trouvé.</p>';
    }

    // --- Partie 1 : Création des cartes pour chaque enregistrement A ---
    const recordsHTML = dnsData.A_records.map((record, index) => `
        <div class="dns-record-card">
            <span class="dns-record-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>
                A Record #${index + 1}
            </span>
            <div class="dns-record-values">
                <span>IP: <strong>${record.address}</strong></span>
                <span>TTL: <strong>${record.ttl}</strong></span>
            </div>
        </div>
    `).join('');

    // --- Partie 2 : Création du bloc de statistiques TTL ---
    const statsHTML = `
        <div class="ttl-stats-container">
            <h5 class="details-subsection-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>
                TTL Statistics
            </h5>
            <div class="ttl-stat-item"><span>Average:</span> <strong>${dnsData.Avg_TTL}</strong></div>
            <div class="ttl-stat-item"><span>Minimum:</span> <strong>${dnsData.Min_TTL}</strong></div>
            <div class="ttl-stat-item"><span>Maximum:</span> <strong>${dnsData.Max_TTL}</strong></div>
        </div>
    `;

    // --- Assemblage final ---
    return `
        <div class="details-section">
            <h4 class="details-section-title">DNS Configuration</h4>
            <p class="dns-summary-line">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                Found ${dnsData.A_record_count} A Records
            </p>
            <div class="dns-records-list">
                ${recordsHTML}
            </div>
            ${statsHTML}
        </div>
    `;
}

/**
 * NOUVELLE FONCTION
 * Crée le contenu HTML pour l'onglet "SSL & Hosting".
 * @param {object} sslData - L'objet ssl_hosting.data de l'API.
 * @returns {string} Le code HTML du panneau.
 */
function createSslTabContent(sslData) {
    if (!sslData) {
        return '<p class="text-muted">Données SSL & Hosting non disponibles.</p>';
    }

    // Formateur de date simple
    const formatDate = (dateString) => {
        try {
            return new Date(dateString).toLocaleDateString('fr-FR', { year: 'numeric', month: 'long', day: 'numeric' });
        } catch (e) {
            return dateString;
        }
    };

    // --- Partie 1 : Détails principaux du certificat ---
    const mainDetailsHTML = `
        <div class="detail-item">
            <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>Secure Connection</span>
            <span class="detail-value">${sslData.HasSSL ? '<span class="status-valid">✅ Valid</span>' : '<span class="status-invalid">❌ Invalid</span>'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><shield/></svg>Protocol</span>
            <span class="detail-value">${sslData.Protocol || 'N/A'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>Issuer</span>
            <span class="detail-value">${sslData.CertIssuer || 'N/A'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>Valid From</span>
            <span class="detail-value">${formatDate(sslData.ValidFrom)}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path></svg>Expires On</span>
            <span class="detail-value">${formatDate(sslData.ValidTo)}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8v4l3 3"></path><circle cx="12" cy="12" r="10"></circle></svg>Days Remaining</span>
            <span class="detail-value">${sslData.DaysUntilExpiry}</span>
        </div>
    `;
    
    // --- Partie 2 : Période de validité ---
    const validityPeriodHTML = `
        <div class="highlight-box">
            <span class="detail-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8v4l3 3"></path><circle cx="12" cy="12" r="10"></circle></svg>
                Validity Period
            </span>
            <span class="highlight-value">${sslData.ValidityPeriod || 'N/A'}</span>
        </div>
    `;

    // --- Partie 3 : Détails du chiffrement (données enrichies) ---
    const cipherDetailsHTML = `
        <div class="details-section" style="margin-top: 2rem;">
            <h5 class="details-subsection-title">Cipher Details</h5>
            <div class="detail-item">
                <span class="detail-label">Cipher Suite</span>
                <span class="detail-value">${sslData.CipherSuite || 'N/A'}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Cipher Version</span>
                <span class="detail-value">${sslData.CipherVersion || 'N/A'}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Cipher Bits</span>
                <span class="detail-value">${sslData.CipherBits || 'N/A'}</span>
            </div>
        </div>
    `;

    // --- Assemblage final ---
    return `
        <div class="details-section">
            <h4 class="details-section-title">Certificate & Security Details</h4>
            ${mainDetailsHTML}
            ${validityPeriodHTML}
            ${cipherDetailsHTML}
        </div>
    `;
}
// js/views/analyzer_on_demand.js

/**
 * NOUVELLE FONCTION
 * Crée le contenu HTML pour l'onglet "Server Location".
 * @param {object} locationData - L'objet server_location.data de l'API.
 * @returns {string} Le code HTML du panneau.
 */
function createServerLocationTabContent(locationData) {
    if (!locationData) {
        return '<p class="text-muted">Données de géolocalisation non disponibles.</p>';
    }

    // Fonction interne pour créer une carte d'information
    const createCard = (icon, label, value) => {
        return `
            <div class="location-card">
                <div class="location-label">
                    ${icon}
                    <span>${label}</span>
                </div>
                <div class="location-value">${value || 'N/A'}</div>
            </div>
        `;
    };
    
    // On gère le cas où l'IP est une liste ou une seule chaîne
    const ipValue = Array.isArray(locationData.IP) ? locationData.IP.join(', ') : locationData.IP;
    const ipLabel = `Resolved IP${Array.isArray(locationData.IP) && locationData.IP.length > 1 ? `s (${locationData.IP.length})` : ''}`;

    // Création de toutes les cartes
    const cardsHTML = `
        ${createCard('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>', ipLabel, ipValue)}
        ${createCard('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>', 'Country', locationData.Country)}
        ${createCard('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 3 22 12 12 22 2 12 5 3"></polygon></svg>', 'Region', locationData.Region)}
        ${createCard('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>', 'City', locationData.City)}
        ${createCard('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>', 'Organization', locationData.Org)}
        ${createCard('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h.79a4.5 4.5 0 1 1 0 9Z"></path></svg>', 'ASN', locationData.ASN)}
    `;

    return `
        <div class="details-section">
            <h4 class="details-section-title">IP Geolocation Details</h4>
            <div class="location-grid">
                ${cardsHTML}
            </div>
        </div>
    `;
}


/**
 * NOUVELLE FONCTION
 * Crée le contenu HTML pour l'onglet "Content".
 * @param {object} contentData - L'objet content.data de l'API.
 * @returns {string} Le code HTML du panneau.
 */
function createContentTabContent(contentData) {
    if (!contentData) {
        return '<p class="text-muted">Données d\'analyse de contenu non disponibles.</p>';
    }

    // Fonctions utilitaires pour l'affichage
    const yesNoIcon = (value) => value ? '<span class="status-valid">✅ Yes</span>' : '<span class="status-invalid">❌ No</span>';
    const noneIcon = (value) => value ? '<span class="status-valid">✅ Yes</span>' : '<span class="status-invalid">❌ None</span>';
    const foundIcon = (value) => value ? '<span class="status-valid">✅ Found</span>' : '<span class="status-invalid">❌ Not found</span>';
    const presentIcon = (value) => value ? '<span class="status-valid">✅ Present</span>' : '<span class="status-invalid">❌ Missing</span>';

    // --- Section 1: Comportement de la page ---
    const behaviorHTML = `
        <div class="detail-item">
            <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2l-3 3h-3l-4 4 2 2 4-4h3l3-3z"></path><path d="M10 14l-6 6"></path><path d="M7 17l-4 4"></path></svg>Redirects</span>
            <span class="detail-value">${noneIcon(contentData.IsURLRedirects)}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>Responsive Design</span>
            <span class="detail-value">${yesNoIcon(contentData.IsResponsive)}</span>
        </div>
    `;

    // --- Section 2: Liens Externes ---
    const links = contentData.ExternalLinks || [];
    const linksCount = contentData.CntExternalRef || links.length;
    let linksHTML = '';
    if (linksCount > 0) {
        const displayedLinks = links.slice(0, 5).map(link => `<li><a href="${link}" target="_blank" rel="noopener noreferrer">${link}</a></li>`).join('');
        const moreLinks = linksCount > 5 ? `<li>... and ${linksCount - 5} more</li>` : '';
        linksHTML = `
            <div class="detail-item-full">
                <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.72"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.72-1.72"></path></svg>External Links (${linksCount})</span>
                <ul class="external-links-list">${displayedLinks}${moreLinks}</ul>
            </div>`;
    }

    // --- Section 3: Métadonnées de la page ---
    const metadataHTML = `
        <div class="detail-item-full">
            <span class="detail-label"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 3h16a2 2 0 0 1 2 2v6a10 10 0 0 1-10 10A10 10 0 0 1 2 11V5a2 2 0 0 1 2-2z"></path><polyline points="8 10 12 14 16 10"></polyline></svg>Page Metadata</span>
            <div class="metadata-list">
                <span>Copyright: ${foundIcon(contentData['HasCopyrightInfoKey '])}</span>
                <span>Description: ${presentIcon(contentData.HasDescription)}</span>
                <span>Favicon: ${foundIcon(contentData.HasFavicon)}</span>
            </div>
        </div>
    `;

    // --- Section 4: BONUS - Composition de la page (infos extra de l'API) ---
    const compositionHTML = `
        <div class="detail-item"><span class="detail-label">Images</span><span class="detail-value">${contentData.CntImages}</span></div>
        <div class="detail-item"><span class="detail-label">Fichiers CSS</span><span class="detail-value">${contentData.CntFilesCSS}</span></div>
        <div class="detail-item"><span class="detail-label">Fichiers JS</span><span class="detail-value">${contentData.CntFilesJS}</span></div>
        <div class="detail-item"><span class="detail-label">Liens internes</span><span class="detail-value">${contentData.CntSelfHRef}</span></div>
        <div class="detail-item"><span class="detail-label">Champs "mot de passe"</span><span class="detail-value">${yesNoIcon(contentData.HasPasswordFields)}</span></div>
    `;

    // --- Assemblage final ---
    return `
        <div class="details-section">
            <h4 class="details-section-title">Page Content & Behavior</h4>
            ${behaviorHTML}
            ${linksHTML}
            ${metadataHTML}
        </div>
        <div class="details-section" style="margin-top: 2rem;">
            <h4 class="details-section-title">Page Composition</h4>
            ${compositionHTML}
        </div>
    `;
}

/**
 * Crée le composant des onglets détaillés (WHOIS, DNS, etc.).
 * VERSION MISE À JOUR AVEC TOUS LES ONGLETS
 */
function createDetailsTabsComponent(apiData) {
    // On appelle notre nouvelle fonction pour le contenu du premier onglet
    const whoisContent = createWhoisTabContent(apiData.domain_whois?.data);
    const dnsContent = createDnsTabContent(apiData.dns?.data);
    const sslContent = createSslTabContent(apiData.ssl_hosting?.data);
    const serverLocationContent = createServerLocationTabContent(apiData.server_location?.data);
    const contentAnalysisContent = createContentTabContent(apiData.content?.data);
    
    

    return `
        <div class="details-tabs-container">
            <nav class="details-tab-nav">
                <button class="details-tab-button active" data-tab="whois-pane">Domain & WHOIS</button>
                <button class="details-tab-button" data-tab="dns-pane">DNS</button>
                <button class="details-tab-button" data-tab="ssl-pane">SSL & Hosting</button>
                <button class="details-tab-button" data-tab="location-pane">Server Location</button>
                <button class="details-tab-button" data-tab="content-pane">Content</button>
                </nav>
            <div class="details-tab-content">
                <div id="whois-pane" class="details-tab-pane active">${whoisContent}</div>
                <div id="dns-pane" class="details-tab-pane">${dnsContent}</div>
                <div id="ssl-pane" class="details-tab-pane">${sslContent}</div>
                <div id="location-pane" class="details-tab-pane">${serverLocationContent}</div>
                <div id="content-pane" class="details-tab-pane">${contentAnalysisContent}</div>
            </div>
        </div>
    `;
}


// js/views/analyzer_on_demand.js

/**
 * NOUVELLE FONCTION
 * Crée le composant HTML pour la carte de prédiction de l'IA.
 * @param {object} predictData - L'objet de la réponse de l'API /predict.
 * @returns {string} Le code HTML du composant.
 */
function createPredictionCardComponent(predictData) {
    if (!predictData) return '';

    const isPhishing = predictData.verdict.toLowerCase().includes('phishing');
    const verdictClass = isPhishing ? 'verdict-phishing' : 'verdict-legitimate';
    const confidenceValue = parseFloat(predictData.confidence);

    return `
        <div class="prediction-card ${verdictClass}">
            <div class="prediction-verdict">
                <h3>${predictData.verdict}</h3>
            </div>
            <div class="confidence-label">
                Confidence: ${predictData.confidence} - ${predictData.risk_level}
            </div>
            <div class="confidence-bar-container">
                <div class="confidence-bar-fill" style="width: ${confidenceValue}%;"></div>
            </div>
            <table class="probability-table">
                <tbody>
                    <tr>
                        <td>Phishing Probability</td>
                        <td>${predictData.probability.phishing}</td>
                    </tr>
                    <tr>
                        <td>Legitimate Probability</td>
                        <td>${predictData.probability.legitimate}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
}

/**
 * Lance l'analyse de l'URL et affiche tous les résultats.
 * VERSION FINALE
 */
async function handleUrlAnalysis() {
    const urlInput = document.getElementById('url-input');
    const analyzeBtn = document.getElementById('analyze-url-btn');
    const resultsContainer = document.getElementById('url-results-container');
    const url = urlInput.value.trim();

    if (!url) {
        alert("Veuillez entrer une URL.");
        return;
    }

    // 1. Afficher l'état de chargement
    analyzeBtn.disabled = true;
    analyzeBtn.querySelector('span').textContent = 'Analyse...';
    resultsContainer.innerHTML = '<div class="loader"></div> <p class="loading-text">Analyse en cours (IA & Contexte)...</p>';

    try {
        // 2. Lancer les deux appels API en parallèle pour gagner du temps
        const contextPromise = fetch('http://127.0.0.1:8000/api/url/context', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        const predictPromise = fetch('http://127.0.0.1:8000/api/url/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        // Attendre que les deux appels soient terminés
        const [contextResponse, predictResponse] = await Promise.all([contextPromise, predictPromise]);

        if (!contextResponse.ok || !predictResponse.ok) {
            throw new Error('Une ou plusieurs requêtes API ont échoué.');
        }

        const contextData = await contextResponse.json();
        const predictData = await predictResponse.json();

        // 3. Assembler la page de résultats complète
        const overviewHTML = createOverviewComponent(contextData.overview?.data);
        const detailsTabsHTML = createDetailsTabsComponent(contextData);
        const predictionCardHTML = createPredictionCardComponent(predictData);

        resultsContainer.innerHTML = `
            <div class="analysis-section">
                <h2>Analyse Contextuelle</h2>
                ${overviewHTML}
                ${detailsTabsHTML}
            </div>
            <div class="analysis-section">
                <h2>Analyse Prédictive (IA)</h2>
                ${predictionCardHTML}
            </div>
        `;

        // Ré-activer la logique des onglets de détails
        setupDynamicTabs('.details-tabs-container');

    } catch (error) {
        console.error("Erreur lors de l'analyse:", error);
        resultsContainer.innerHTML = `<p class="error-message">L'analyse a échoué. Vérifiez la console pour plus de détails.</p>`;
    } finally {
        // 4. Rétablir le bouton
        analyzeBtn.disabled = false;
        analyzeBtn.querySelector('span').textContent = 'Analyser';
    }
}



/**
 * Génère le HTML de la vue "Analyse à la demande", incluant le formulaire,
 * et attache les écouteurs d'événements nécessaires.
 */
export function loadUrlAnalyzerView(viewContainer) {
    // On vérifie si le contenu a déjà été dessiné
    if (viewContainer.innerHTML.trim() !== '') {
        return; // Si oui, on ne fait rien
    }

      // Si c'est la première visite, on dessine le HTML
    viewContainer.innerHTML = `
        <div class="on-demand-container">
            <nav class="on-demand-tabs">
                <button class="on-demand-tab-button active" data-tab="url-pane">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                    Analyse d'URL
                </button>
                <button class="on-demand-tab-button" data-tab="header-pane">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
                    Analyse d'En-tête
                </button>
                <button class="on-demand-tab-button" data-tab="message-pane">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                    Analyse de Message
                </button>
            </nav>

            <div class="on-demand-content">
                <div class="on-demand-pane active" id="url-pane">
                    
                    <div class="url-analyzer-form">
                        <div class="input-group">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
                            <input type="text" id="url-input" placeholder="Entrez une URL complète à analyser (ex: https://www.exemple.com)">
                        </div>
                        <button id="analyze-url-btn" class="btn btn-primary">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                            <span>Analyser</span>
                        </button>
                    </div>

                    <div id="url-results-container"></div>

                </div>
                <div class="on-demand-pane" id="header-pane">
                    <p>Contenu à venir pour l'analyse d'en-tête...</p>
                </div>
                <div class="on-demand-pane" id="message-pane">
                    <p>Contenu à venir pour l'analyse de message...</p>
                </div>
            </div>
        </div>
    `;

    // Active la logique des onglets
    setupOnDemandTabs();

    // Attache l'événement au bouton "Analyser"
    const analyzeBtn = document.getElementById('analyze-url-btn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', handleUrlAnalysis);
    }
}