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

        # --- AJOUT CLÉ ---
        # On s'assure que le répertoire de destination pour le token existe.
        # os.path.dirname(settings.TOKEN_FILE) récupère /config/.secrets
        os.makedirs(os.path.dirname(settings.TOKEN_FILE), exist_ok=True)
        
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
            date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'N/A')

            plain_part, html_part = _find_text_parts(payload)
            
            body = ""
            if plain_part:
                body = _decode_email_body(plain_part[0], plain_part[1])

            html_body = ""
            if html_part:
                html_body = _decode_email_body(html_part[0], html_part[1])
            
            email_data = {
                'id': msg.get('id'),
                'snippet': msg.get('snippet'),
                'sender': from_header,
                'subject': subject_header,
                'timestamp': date_header,
                'body': body,
                'html_body': html_body,
                'full_headers': headers
            }
            email_list.append(email_data)
        
        print(f"{len(email_list)} e-mail(s) récupéré(s).")

        # debug
        # print("Exemple d'e-mail récupéré:", email_list[0] if email_list else "Aucun e-mail trouvé.")
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


def _find_text_parts(payload):
    """Trouve récursivement les parties textuelles (plain et html)."""
    mime_type = payload.get('mimeType', '').lower()
    
    if mime_type == 'text/plain':
        if payload.get('body') and 'data' in payload['body']:
            return (payload['body']['data'], payload.get('headers', [])), None
    
    if mime_type == 'text/html':
        if payload.get('body') and 'data' in payload['body']:
            return None, (payload['body']['data'], payload.get('headers', []))

    if mime_type.startswith('multipart/'):
        plain_part = None
        html_part = None
        for part in payload.get('parts', []):
            plain, html = _find_text_parts(part)
            if plain and not plain_part:
                plain_part = plain
            if html and not html_part:
                html_part = html
        return plain_part, html_part

    return None, None


# -------------------------------------------------------------------------------------------------------------------
# ------- Libellés
# -------------------------------------------------------------------------------------------------------------------
# PhishGard-AI/core/email_client.py

# PhishGard-AI/core/email_client.py

def get_or_create_label_id(service, label_name):
    """
    Vérifie si un libellé existe. Si non, le crée en utilisant la palette de couleurs officielle de Gmail.
    Retourne l'ID du libellé.
    """
    parent_label_name = "PhishGard-AI"
    full_label_name = f"{parent_label_name}/{label_name}"

    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    parent_label_id = None
    label_id = None
    for label in labels:
        if label['name'] == parent_label_name:
            parent_label_id = label['id']
        if label['name'] == full_label_name:
            label_id = label['id']

    if label_id:
        print(f"  [LABEL] Le libellé '{full_label_name}' existe déjà (ID: {label_id}).")
        return label_id

    if not parent_label_id:
        print(f"  [LABEL] Création du libellé parent '{parent_label_name}'...")
        parent_label_body = {
            'name': parent_label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        parent_label = service.users().labels().create(userId='me', body=parent_label_body).execute()
        parent_label_id = parent_label['id']

    print(f"  [LABEL] Création du libellé '{full_label_name}'...")

    # --- DÉFINITION DES COULEURS DE LA PALETTE GMAIL OFFICIELLE ---
    if label_name == 'Legitime':
        bg_color = '#16a765'  # Vert (valide)
        txt_color = '#ffffff' # Blanc
    elif label_name == 'Suspicious':
        bg_color = '#fad165'  # Jaune/Or (remplace #f39c12)
        txt_color = '#000000' # Noir
    else:  # Phishing
        bg_color = '#fb4c2f'  # Rouge/Orange (remplace #db4437)
        txt_color = '#ffffff' # Blanc

    label_body = {
        'name': full_label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show',
        'color': {
            'backgroundColor': bg_color,
            'textColor': txt_color
        }
    }
    new_label = service.users().labels().create(userId='me', body=label_body).execute()
    
    return new_label['id']


def apply_label_to_email(service, email_id, label_id_to_add):
    """
    Applique un libellé à un e-mail spécifique.
    """
    try:
        print(f"  [LABEL] Application du libellé (ID: {label_id_to_add}) à l'e-mail (ID: {email_id})...")
        # On utilise 'modify' pour ajouter un libellé sans en enlever d'autres
        modification_body = {'addLabelIds': [label_id_to_add]}
        service.users().messages().modify(userId='me', id=email_id, body=modification_body).execute()
        print("  [LABEL] ... Application réussie.")
        return True
    except Exception as e:
        print(f"  [LABEL] Erreur lors de l'application du libellé: {e}")
        return False