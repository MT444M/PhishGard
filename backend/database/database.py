# database/database.py
# Ce fichier initialise la connexion à la base de données.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de connexion pour SQLite. Le fichier phishgard.db sera créé à la racine.
# POUR LA PRODUCTION avec PostgreSQL, la ligne ressemblerait à :
# DATABASE_URL = "postgresql://user:password@postgresserver/db"
# DATABASE_URL = "sqlite:///./phishgard.db"
DATABASE_URL = "postgresql://phishgard_user:password@localhost:5432/phishgard_db"

engine = create_engine(
    DATABASE_URL # check_same_thread est nécessaire pour SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()