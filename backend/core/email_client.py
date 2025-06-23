# PhishGard-AI/core/email_client.py

import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# On importe la configuration centralisée
from config import settings

def authenticate_gmail():
    """Authentifie l'utilisateur et retourne le service Gmail API."""
    creds = None
    if os.path.exists(settings.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(settings.TOKEN_FILE, settings.GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Erreur lors du rafraîchissement du token: {e}, on relance le flux.")
                flow = InstalledAppFlow.from_client_secrets_file(settings.CREDENTIALS_FILE, settings.GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(settings.CREDENTIALS_FILE, settings.GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(settings.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        print("Authentification Gmail réussie.")
        return service
    except HttpError as error:
        print(f'Une erreur est survenue lors de la création du service Gmail: {error}')
        return None

def get_emails(service, user_id='me', max_results=1, email_id=None):
    """Récupère les e-mails avec leur corps décodé et tous leurs en-têtes."""
    # Cette fonction intègre toute la logique de parsing de corps d'email
    # qui était dans gmail_reader_analyzer.py
    try:
        if email_id:
            # Si un ID est fourni, on récupère juste ce message
            messages_info = [{'id': email_id}]
        else:
            # Sinon, on liste les messages comme avant
            results = service.users().messages().list(userId=user_id, maxResults=max_results).execute()
            messages_info = results.get('messages', [])

        if not messages_info:
            print("Aucun message trouvé.")
            return []

        email_list = []
        for msg_info in messages_info:
            msg = service.users().messages().get(userId=user_id, id=msg_info['id'], format='full').execute()
            
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            
            # Simplification: extraire les headers clés pour un accès facile
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'N/A')
            subject_header = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'N/A')

            data, headers_part, _ = _find_best_text_part(payload)
            body = _decode_email_body(data, headers_part) if data else ""
            
            email_data = {
                'id': msg.get('id'),
                'snippet': msg.get('snippet'),
                'sender': from_header,
                'subject': subject_header,
                'body': body,
                'full_headers': headers
            }
            email_list.append(email_data)
        
        print(f"{len(email_list)} e-mail(s) récupéré(s).")
        return email_list

    except HttpError as error:
        print(f'Une erreur HttpError s\'est produite : {error}')
        return []

# --- Fonctions utilitaires privées (commencent par _) pour ce module ---

def _decode_email_body(data_b64url, headers_list):
    """Décode le corps de l'e-mail encodé en base64url."""
    char_set = 'utf-8' # Default
    if headers_list:
        content_type = next((h['value'] for h in headers_list if h['name'].lower() == 'content-type'), None)
        if content_type and 'charset=' in content_type:
            char_set = content_type.split('charset=')[-1].split(';')[0].strip().replace('"', '')

    try:
        missing_padding = len(data_b64url) % 4
        if missing_padding:
            data_b64url += '=' * (4 - missing_padding)
        decoded_bytes = base64.urlsafe_b64decode(data_b64url.encode('ASCII'))
        return decoded_bytes.decode(char_set, errors='replace')
    except Exception:
        # Fallback
        return base64.urlsafe_b64decode(data_b64url.encode('ASCII')).decode('latin-1', errors='replace')


def _find_best_text_part(payload):
    """Trouve récursivement la meilleure partie textuelle (plain > html)."""
    mime_type = payload.get('mimeType', '').lower()
    if mime_type == 'text/plain':
        if payload.get('body') and 'data' in payload['body']:
            return payload['body']['data'], payload.get('headers', []), 'text/plain'
    
    if mime_type.startswith('multipart/'):
        parts = payload.get('parts', [])
        candidate_plain = None
        candidate_html = None
        for part in parts:
            data, headers, found_mime = _find_best_text_part(part)
            if data and found_mime == 'text/plain':
                candidate_plain = (data, headers, 'text/plain')
                break
            if data and found_mime == 'text/html' and not candidate_html:
                candidate_html = (data, headers, 'text/html')
        return candidate_plain if candidate_plain else candidate_html

    if mime_type == 'text/html':
        if payload.get('body') and 'data' in payload['body']:
            return payload['body']['data'], payload.get('headers', []), 'text/html'

    return None, None, None