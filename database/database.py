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

# Récupérer les valeurs des variables pour la journalisation
log_db_host = os.getenv("DB_HOST", "localhost")
log_db_port = os.getenv("DB_PORT", "5432")
log_db_name = os.getenv("DB_NAME", "phishgard_db")
log_db_user = os.getenv("DB_USER", "phishgard_user")
log_db_password = os.getenv("DB_PASSWORD", "password")

# Si DATABASE_URL est fourni directement, on l'utilise, sinon on le construit à partir des variables individuelles
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Construction de l'URL de connexion à partir des variables déjà récupérées
    DATABASE_URL = f"postgresql://{log_db_user}:{log_db_password}@{log_db_host}:{log_db_port}/{log_db_name}"

# Journalisation des informations de connexion (sans le mot de passe)
logging.info(f"DATABASE_URL présent: {DATABASE_URL is not None}")
logging.info(f"Tentative de connexion à la base de données: {log_db_host}:{log_db_port}/{log_db_name} avec l'utilisateur {log_db_user}")

try:
    # Masquer le mot de passe dans l'URL pour le logging (en toute sécurité)
    masked_url = DATABASE_URL
    if log_db_password and log_db_password in masked_url:
        masked_url = masked_url.replace(log_db_password, '***')
    logging.info(f"URL finale de connexion: {masked_url}")
except Exception as e:
    logging.warning(f"Impossible d'afficher l'URL masquée: {e}")

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
        # Au lieu de retourner None, on lève une exception HTTP
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La connexion à la base de données n'est pas disponible. Veuillez vérifier les paramètres de connexion."
        )
    finally:
        logger.debug("Fermeture de la session de base de données")
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
