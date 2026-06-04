import pytest
from unittest.mock import patch, MagicMock, call
from google.auth.exceptions import RefreshError

from services.auth_service import AuthService, AuthError, ClientSecretsNotFoundError


@pytest.fixture
def auth(fake_secrets_file):
    service = AuthService()
    with patch("services.auth_service.CLIENT_SECRETS_PATH", fake_secrets_file):
        yield service


class TestIsLoggedIn:
    def test_returns_true_when_token_stored(self):
        with patch("services.auth_service.keyring.get_password", return_value="tok"):
            assert AuthService().is_logged_in() is True

    def test_returns_false_when_no_token(self):
        with patch("services.auth_service.keyring.get_password", return_value=None):
            assert AuthService().is_logged_in() is False


class TestGetCredentials:
    def test_raises_when_no_token_in_keyring(self, auth):
        with patch("services.auth_service.keyring.get_password", return_value=None):
            with pytest.raises(AuthError, match="No refresh token"):
                auth.get_credentials()

    def test_raises_when_secrets_file_missing(self):
        from pathlib import Path
        service = AuthService()
        with patch("services.auth_service.keyring.get_password", return_value="tok"):
            with patch("services.auth_service.CLIENT_SECRETS_PATH", Path("nonexistent.json")):
                with pytest.raises(ClientSecretsNotFoundError):
                    service.get_credentials()

    def test_returns_credentials_on_success(self, auth, mock_credentials):
        with patch("services.auth_service.keyring.get_password", return_value="tok"):
            with patch("services.auth_service.Credentials") as MockCreds:
                MockCreds.return_value = mock_credentials
                with patch("services.auth_service.Request"):
                    creds = auth.get_credentials()
        assert creds is mock_credentials

    def test_clears_token_and_raises_on_refresh_error(self, auth):
        with patch("services.auth_service.keyring.get_password", return_value="bad_tok"):
            with patch("services.auth_service.Credentials") as MockCreds:
                MockCreds.return_value.refresh.side_effect = RefreshError("invalid_grant")
                with patch("services.auth_service.Request"):
                    with patch("services.auth_service.keyring.delete_password") as mock_del:
                        with pytest.raises(AuthError, match="Session expired"):
                            auth.get_credentials()
                mock_del.assert_called_once()


class TestAuthenticate:
    def test_raises_when_secrets_missing(self):
        from pathlib import Path
        service = AuthService()
        with patch("services.auth_service.CLIENT_SECRETS_PATH", Path("nonexistent.json")):
            with pytest.raises(ClientSecretsNotFoundError):
                service.authenticate()

    def test_saves_refresh_token_on_success(self, auth, mock_credentials):
        with patch("services.auth_service.InstalledAppFlow") as MockFlow:
            MockFlow.from_client_secrets_file.return_value.run_local_server.return_value = mock_credentials
            with patch("services.auth_service.keyring.set_password") as mock_set:
                creds = auth.authenticate()

        mock_set.assert_called_once_with(
            "YouTubeNotifier", "refresh_token", mock_credentials.refresh_token
        )
        assert creds is mock_credentials

    def test_opens_browser_flow(self, auth, mock_credentials):
        with patch("services.auth_service.InstalledAppFlow") as MockFlow:
            instance = MockFlow.from_client_secrets_file.return_value
            instance.run_local_server.return_value = mock_credentials
            with patch("services.auth_service.keyring.set_password"):
                auth.authenticate()

        instance.run_local_server.assert_called_once_with(port=0, open_browser=True)


class TestLogout:
    def test_deletes_keyring_entry(self):
        with patch("services.auth_service.keyring.delete_password") as mock_del:
            AuthService().logout()
        mock_del.assert_called_once_with("YouTubeNotifier", "refresh_token")

    def test_logout_silent_when_no_token(self):
        import keyring.errors
        with patch(
            "services.auth_service.keyring.delete_password",
            side_effect=keyring.errors.PasswordDeleteError("not found"),
        ):
            AuthService().logout()  # should not raise
