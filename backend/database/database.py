# # database/database.py
# # Ce fichier initialise la connexion à la base de données.

# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# # URL de connexion pour SQLite. Le fichier phishgard.db sera créé à la racine.
# # POUR LA PRODUCTION avec PostgreSQL, la ligne ressemblerait à :
# # DATABASE_URL = "postgresql://user:password@postgresserver/db"
# # DATABASE_URL = "sqlite:///./phishgard.db"
# DATABASE_URL = "postgresql://phishgard_user:password@localhost:5432/phishgard_db"

# engine = create_engine(
#     DATABASE_URL # check_same_thread est nécessaire pour SQLite
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

# # Dépendance FastAPI pour obtenir une session de BDD par requête
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# def create_tables():
#     Base.metadata.create_all(bind=engine)



# database/database.py
# Ce fichier initialise la connexion à la base de données.

import os 
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv 

# Charger les variables d'environnement du fichier .env pour le développement
load_dotenv() 


# L'URL de la base de données est lue depuis les variables d'environnement.
# Si la variable n'existe pas, une URL SQLite par défaut est utilisée pour le développement.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./phishgard.db")



# On vérifie si on utilise PostgreSQL pour retirer un argument non compatible
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL)
else:
    # L'argument check_same_thread est spécifique à SQLite
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dépendance FastAPI pour obtenir une session de BDD par requête
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()