# backend/auth/auth_service.py

from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request as FastAPIRequest
from sqlalchemy.orm import Session

from config import settings
from database import crud, models
from database.database import get_db

# --- Chiffrement ---

if not settings.FERNET_KEY:
    raise ValueError("La clé de chiffrement FERNET_KEY n'est pas configurée dans les paramètres.")

fernet = Fernet(settings.FERNET_KEY.encode())

def encrypt_token(token: str) -> str:
    """Chiffre un token en utilisant la clé Fernet."""
    if not token: return None
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Déchiffre un token en utilisant la clé Fernet."""
    if not encrypted_token: return None
    return fernet.decrypt(encrypted_token.encode()).decode()


# --- Flux OAuth 2.0 ---

def get_google_oauth_flow() -> Flow:
    """Crée et retourne une instance du flux OAuth 2.0 de Google."""
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=settings.GMAIL_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    return flow

# --- Gestion des Tokens JWT ---

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Crée un token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


# --- Dépendances ---

async def get_current_user(request: FastAPIRequest, db: Session = Depends(get_db)) -> models.User:
    """
    Dépendance pour obtenir l'utilisateur actuel à partir du token JWT dans le cookie.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les informations d'identification",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        google_id: str = payload.get("sub")
        if google_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_google_id(db, google_id=google_id)
    if user is None:
        raise credentials_exception
        
    return user


async def get_gmail_service(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)) -> Resource:
    """
    Construit, rafraîchit si nécessaire, et retourne un service Gmail authentifié.
    """
    try:
        access_token = decrypt_token(current_user.encrypted_access_token)
        refresh_token = decrypt_token(current_user.encrypted_refresh_token)

        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=settings.GOOGLE_TOKEN_URI,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GMAIL_SCOPES
        )

        # Rafraîchir le token s'il est expiré
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Mettre à jour les tokens chiffrés dans la BDD
            crud.create_or_update_user(
                db=db,
                email=current_user.email,
                google_id=current_user.google_id,
                access_token=encrypt_token(creds.token),
                refresh_token=encrypt_token(creds.refresh_token),
                token_expiry=creds.expiry
            )

        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Erreur lors de la création du service Gmail: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de construire le service Gmail pour l'utilisateur."
        )
