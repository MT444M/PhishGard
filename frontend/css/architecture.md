
# .Architecture des fichiers CSS

/css
|
|── style.css        # Le fichier principal qui importe tous les autres.
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
|
└── /layout/
    └── main.css       # Styles pour la structure principale (.main-content, .main-nav, etc.).

