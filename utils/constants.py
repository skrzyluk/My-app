import os
import sys
from pathlib import Path

APP_NAME = "YouTubeNotifier"
APP_VERSION = "0.1.0"

APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
LOG_PATH = APPDATA_DIR / "app.log"


def get_client_secrets_path() -> Path:
    """Resolve client_secrets.json location.

    Frozen exe: read from the user's %APPDATA%\\YouTubeNotifier\\ location (as in
    the docs) - secrets are not baked into the exe.
    During development it lives in the project root.
    """
    if hasattr(sys, "_MEIPASS"):
        return APPDATA_DIR / "client_secrets.json"
    return Path(__file__).resolve().parent.parent / "client_secrets.json"


CLIENT_SECRETS_PATH = get_client_secrets_path()

KEYRING_SERVICE = APP_NAME
KEYRING_USER = "refresh_token"

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# YouTube API
YOUTUBE_API_SERVICE = "youtube"
YOUTUBE_API_VERSION = "v3"
MAX_RESULTS = 50

# Cache TTL in hours
CACHE_TTL_HOURS = 24

# Retry backoff delays in seconds
RETRY_DELAYS = [1, 2, 4, 8]
