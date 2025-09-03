# backend/auth/auth_router.py

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import requests

from database import crud
from database.database import get_db
from . import auth_service
from config import settings

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

@router.get("/login")
def login():
    """
    Redirige l'utilisateur vers la page de consentement de Google.
    """
    flow = auth_service.get_google_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent', # Force la demande de consentement pour obtenir un refresh_token
        include_granted_scopes='true'
    )
    return RedirectResponse(authorization_url)


@router.get("/callback")
def auth_callback(code: str, response: Response, db: Session = Depends(get_db)):
    """
    Callback de Google après authentification.
    Échange le code contre des tokens, crée un JWT et le stocke dans un cookie.
    """
    try:
        flow = auth_service.get_google_oauth_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v1/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        
        if not user_info_response.ok:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Impossible de récupérer les informations de l'utilisateur depuis Google."
            )
            
        user_info = user_info_response.json()
        email = user_info.get("email")
        google_id = user_info.get("id")

        if not email or not google_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Les informations de l'utilisateur (email, id) n'ont pas pu être récupérées."
            )

        encrypted_access_token = auth_service.encrypt_token(credentials.token)
        encrypted_refresh_token = auth_service.encrypt_token(credentials.refresh_token) if credentials.refresh_token else None

        user = crud.create_or_update_user(
            db=db,
            email=email,
            google_id=google_id,
            access_token=encrypted_access_token,
            refresh_token=encrypted_refresh_token,
            token_expiry=credentials.expiry
        )

        # Créer un token JWT pour la session
        jwt_token = auth_service.create_access_token(data={"sub": user.google_id})
        
        # Stocker le JWT dans un cookie HttpOnly sécurisé
        response = RedirectResponse(url=settings.FRONTEND_URL) # Redirige vers le frontend
        
        # Determine cookie security settings based on domain
        is_production = settings.CALLBACK_DOMAIN != "localhost"
        
        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,
            secure=is_production, # Secure only in production (HTTPS required)
            domain=settings.CALLBACK_DOMAIN if is_production else None,
            samesite='lax'
        )
        return response

    except Exception as e:
        print(f"Erreur lors du callback OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur est survenue durant le processus d'authentification: {str(e)}"
        )

@router.post("/logout")
def logout():
    """
    Déconnecte l'utilisateur en supprimant le cookie de session.
    """
    from config import settings
    
    response = JSONResponse(content={"message": "Déconnexion réussie"})
    
    # Determine cookie domain based on environment
    is_production = settings.CALLBACK_DOMAIN != "localhost"
    domain = settings.CALLBACK_DOMAIN if is_production else None
    
    response.delete_cookie("access_token", domain=domain)
    return response
