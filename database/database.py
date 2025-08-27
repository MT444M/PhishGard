# database/database.py
# Ce fichier initialise la connexion à la base de données.

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

# Configuration du logger pour le module database
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

# Valeurs par défaut pour le développement local
DB_USER = os.getenv("DB_USER", "phishgard_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "phishgard_db")

# Construction de l'URL de connexion
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Journalisation des informations de connexion (sans le mot de passe)
logging.info(f"Tentative de connexion à la base de données: {DB_HOST}:{DB_PORT}/{DB_NAME} avec l'utilisateur {DB_USER}")

# Création de l'engine avec des options de débogage
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Afficher toutes les requêtes SQL
    pool_pre_ping=True  # Vérifier la connexion avant de l'utiliser
)

# Ajout d'un écouteur pour détecter les événements de connexion
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.info("Base de données connectée avec succès!")

# Note: SQLAlchemy n'a pas d'événement 'connect_error'
# Nous gérons les erreurs de connexion dans get_db() ou via pool_pre_ping=True

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dépendance FastAPI pour obtenir une session de BDD par requête
def get_db():
    db = SessionLocal()
    try:
        # Tentative d'exécuter une requête simple pour vérifier la connexion
        logger.info("Vérification de la connexion à la base de données...")
        # Méthode compatible avec toutes les versions de SQLAlchemy
        with db.connection() as conn:
            conn.execute("SELECT 1")
        logger.info("Connexion à la base de données vérifiée")
        yield db
    except Exception as e:
        logger.error(f"Erreur lors de l'accès à la base de données: {e}")
        # Ne pas lever d'exception pour éviter de bloquer l'application
        # Retourner None pour indiquer que la connexion a échoué
        yield None
    finally:
        logger.debug("Fermeture de la session de base de données")
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
