import os
from pathlib import Path

APP_NAME = "YouTubeNotifier"
APP_VERSION = "0.1.0"

APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
CLIENT_SECRETS_PATH = APPDATA_DIR / "client_secrets.json"
LOG_PATH = APPDATA_DIR / "app.log"

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
