import msal
from config import settings

def get_access_token():
    app = msal.ConfidentialClientApplication(
        settings.CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.TENANT_ID}",
        client_credential=settings.CLIENT_SECRET
    )
    token_response = app.acquire_token_silent(settings.GRAPH_SCOPE, account=None)
    if not token_response:
        token_response = app.acquire_token_for_client(scopes=settings.GRAPH_SCOPE)
    return token_response['access_token']

def get_headers():
    token = get_access_token()
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }