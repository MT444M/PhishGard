
# .Architecture des fichiers CSS

/css
|
|── style.css        # Le fichier principal qui importe tous les autres.
|── utils.css        # Styles utilitaires réutilisables.
|
|── /base/
|   |── variables.css  # Contient uniquement les variables (:root).
|   └── base.css       # Styles globaux (body, *, container, etc.).
|
|── /components/
|   |── header.css     # Styles pour le header, logo, stats, menu utilisateur.
|   |── email.css      # Styles pour la liste d'e-mails et les cartes.
|   |── filters.css    # Styles pour la barre de filtres de droite.
|   └── modal.css      # Styles pour la modale, ses onglets et son contenu.
|   └── on_demand.css  # Styles pour l'analyse à la demande.
|
└── /layout/
    └── main.css       # Styles pour la structure principale (.main-content, .main-nav, etc.).

