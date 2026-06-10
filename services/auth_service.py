import keyring
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from utils.constants import (
    CLIENT_SECRETS_PATH,
    KEYRING_SERVICE,
    KEYRING_USER,
    SCOPES,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class AuthError(Exception):
    pass


class ClientSecretsNotFoundError(AuthError):
    pass


class AuthService:
    def get_credentials(self) -> Credentials:
        """Return valid credentials, refreshing automatically if needed.

        Raises AuthError if token is revoked or missing – caller should
        redirect to login screen.
        """
        refresh_token = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
        if not refresh_token:
            raise AuthError("No refresh token stored – user must log in.")

        if not CLIENT_SECRETS_PATH.exists():
            raise ClientSecretsNotFoundError(
                f"client_secrets.json not found at {CLIENT_SECRETS_PATH}"
            )

        import json
        with open(CLIENT_SECRETS_PATH) as f:
            secrets = json.load(f)

        web = secrets.get("installed") or secrets.get("web", {})
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=web.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=web.get("client_id"),
            client_secret=web.get("client_secret"),
            scopes=SCOPES,
        )

        try:
            creds.refresh(Request())
        except RefreshError as e:
            logger.warning("Refresh token invalid, clearing stored token: %s", e)
            self.logout()
            raise AuthError("Session expired – please log in again.") from e

        return creds

    def authenticate(self) -> Credentials:
        """Run OAuth browser flow and persist the refresh token.

        Raises ClientSecretsNotFoundError if client_secrets.json is missing.
        """
        if not CLIENT_SECRETS_PATH.exists():
            raise ClientSecretsNotFoundError(
                f"client_secrets.json not found at {CLIENT_SECRETS_PATH}\n"
                f"Place your OAuth credentials file there and restart."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_PATH), scopes=SCOPES
        )
        creds = flow.run_local_server(port=0, open_browser=True)

        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, creds.refresh_token)
        logger.info("OAuth authentication successful, refresh token saved.")
        return creds

    def logout(self) -> None:
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
            logger.info("User logged out, refresh token deleted.")
        except keyring.errors.PasswordDeleteError:
            pass

    def is_logged_in(self) -> bool:
        return keyring.get_password(KEYRING_SERVICE, KEYRING_USER) is not None
