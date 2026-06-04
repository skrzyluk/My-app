import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def fake_secrets_file(tmp_path) -> Path:
    secrets = {
        "installed": {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }
    path = tmp_path / "client_secrets.json"
    path.write_text(json.dumps(secrets))
    return path


@pytest.fixture
def mock_credentials():
    creds = MagicMock()
    creds.token = "access_token_abc"
    creds.refresh_token = "refresh_token_xyz"
    creds.valid = True
    creds.expired = False
    return creds
