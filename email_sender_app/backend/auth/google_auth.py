from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse
import os

# OAuth2 configuration
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email'
]

class GoogleAuthManager:
    def __init__(self):
        self.client_secrets_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "client_secrets.json"
        )
        
    async def get_authorization_url(self) -> str:
        flow = Flow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=SCOPES,
            redirect_uri="http://localhost:3000/auth/callback"
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return authorization_url, state
    
    async def process_oauth_callback(self, code: str) -> Credentials:
        try:
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=SCOPES,
                redirect_uri="http://localhost:3000/auth/callback"
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials
            return credentials
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) 