from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIVATE_DIR = os.path.join(BASE_DIR, "private")

CREDENTIALS_PATH = os.path.join(PRIVATE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(PRIVATE_DIR, "token.json")

SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_drive_service():
    creds = None
    token_path = TOKEN_PATH
    cred_path = CREDENTIALS_PATH

    # Try load existing token.json safely
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            # Corrupted token file — remove and trigger re-auth
            print("Warning: failed to load token.json, will re-auth:", str(e), file=sys.stderr)
            try:
                os.remove(token_path)
            except Exception:
                pass
            creds = None

    # If credentials exist but need refresh, attempt to refresh
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as e:
            # Token revoked/expired server-side — remove token and re-run auth flow
            print("RefreshError: token expired or revoked, removing token.json and re-authorizing.", file=sys.stderr)
            try:
                os.remove(token_path)
            except Exception:
                pass
            creds = None
        except Exception as e:
            print("Unexpected error refreshing credentials:", str(e), file=sys.stderr)
            creds = None

    # If no valid credentials, run the OAuth flow
    if not creds or not creds.valid:
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"{cred_path} not found — place your OAuth client secrets there.")
        flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
        # run_local_server is interactive; keep as before but allow opening browser
        creds = flow.run_local_server(port=0, prompt="consent", access_type="offline", open_browser=False, authorization_prompt_message="Please visit this URL to authorize this application: {url}")
        # Save the credentials for the next run
        try:
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        except Exception as e:
            print("Warning: failed to save token.json:", str(e), file=sys.stderr)

    # Build service
    try:
        service = build("drive", "v3", credentials=creds)
    except Exception as e:
        print("Failed to build Drive service:", str(e), file=sys.stderr)
        raise

    return service