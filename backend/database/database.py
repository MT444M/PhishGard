# database/database.py
# Ce fichier initialise la connexion à la base de données.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de connexion pour SQLite. Le fichier phishgard.db sera créé à la racine.
# POUR LA PRODUCTION avec PostgreSQL, la ligne ressemblerait à :
# DATABASE_URL = "postgresql://user:password@postgresserver/db"
DATABASE_URL = "sqlite:///./phishgard.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} # check_same_thread est nécessaire pour SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # permet de créer des sessions en contrôlant la transaction, et en évitant les problèmes de concurrence.

Base = declarative_base()