import os
import tempfile
import unittest
from unittest.mock import patch

from spotapi import (
    AuthorizationCodeAuth,
    ClientCredentialsAuth,
    SpotifyAuthError,
    TokenCache,
    authorization_code_auth_from_env,
    oauth_credentials_from_env,
    oauth_error_from_transport,
    redirect_uri_from_env,
    refresh_token_from_env,
    scopes_from_env,
    user_client_from_env,
)
from spotapi.oauth_env import DEFAULT_REDIRECT_URI
from spotapi.transport import TransportError


class FakeAuthTransport:
    def __init__(self, response=None, error=None):
        self.response = response or {
            "access_token": "token-from-auth",
            "expires_in": 3600,
        }
        self.error = error
        self.calls = []

    def post_form_json(self, url, body, headers):
        self.calls.append((url, body, headers))
        if self.error is not None:
            raise self.error
        return self.response


class OAuthEnvTest(unittest.TestCase):
    def test_oauth_credentials_from_env(self):
        with patch.dict(
            os.environ,
            {
                "SPOTIFY_CLIENT_ID": "client",
                "SPOTIFY_CLIENT_SECRET": "secret",
            },
            clear=True,
        ):
            self.assertEqual(oauth_credentials_from_env(), ("client", "secret"))

    def test_oauth_credentials_from_env_requires_values(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SpotifyAuthError):
                oauth_credentials_from_env()

    def test_redirect_uri_from_env_prefers_explicit_value(self):
        self.assertEqual(
            redirect_uri_from_env({"redirect_uri": "http://cached"}, "http://explicit"),
            "http://explicit",
        )

    def test_redirect_uri_from_env_uses_env_then_cache_then_default(self):
        with patch.dict(os.environ, {"SPOTIFY_REDIRECT_URI": "http://env"}, clear=True):
            self.assertEqual(redirect_uri_from_env({"redirect_uri": "http://cached"}), "http://env")

        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(redirect_uri_from_env({"redirect_uri": "http://cached"}), "http://cached")
            self.assertEqual(redirect_uri_from_env(), DEFAULT_REDIRECT_URI)

    def test_refresh_token_from_env_prefers_env(self):
        with patch.dict(os.environ, {"SPOTIFY_REFRESH_TOKEN": "env-refresh"}, clear=True):
            self.assertEqual(refresh_token_from_env({"refresh_token": "cached-refresh"}), "env-refresh")

    def test_scopes_from_env_prefers_env(self):
        with patch.dict(os.environ, {"SPOTIFY_SCOPES": "user-read-email playlist-read-private"}, clear=True):
            self.assertEqual(scopes_from_env({"scope": "user-top-read"}), ["user-read-email", "playlist-read-private"])

    def test_authorization_code_auth_from_env_builds_auth(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tokens.json")
            TokenCache(path).save(
                {
                    "refresh_token": "cached-refresh",
                    "redirect_uri": "http://127.0.0.1:8080",
                    "scope": "user-read-email",
                }
            )

            with patch.dict(
                os.environ,
                {
                    "SPOTIFY_CLIENT_ID": "client",
                    "SPOTIFY_CLIENT_SECRET": "secret",
                },
                clear=True,
            ):
                auth = authorization_code_auth_from_env(token_cache_path=path)

            self.assertEqual(auth.client_id, "client")
            self.assertEqual(auth.refresh_token, "cached-refresh")
            self.assertEqual(auth.redirect_uri, "http://127.0.0.1:8080")
            self.assertEqual(auth.scope, ["user-read-email"])

    def test_authorization_code_auth_from_env_requires_refresh_token(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tokens.json")
            with patch.dict(
                os.environ,
                {
                    "SPOTIFY_CLIENT_ID": "client",
                    "SPOTIFY_CLIENT_SECRET": "secret",
                },
                clear=True,
            ):
                with self.assertRaises(SpotifyAuthError):
                    authorization_code_auth_from_env(token_cache_path=path)

    def test_user_client_from_env_wraps_auth(self):
        transport = FakeAuthTransport()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tokens.json")
            TokenCache(path).save({"refresh_token": "cached-refresh", "expires_at": 0})

            with patch.dict(
                os.environ,
                {
                    "SPOTIFY_CLIENT_ID": "client",
                    "SPOTIFY_CLIENT_SECRET": "secret",
                },
                clear=True,
            ):
                client = user_client_from_env(token_cache_path=path, transport=transport, auto_set=False)

            self.assertEqual(client.auth.token(), "token-from-auth")


class OAuthErrorTest(unittest.TestCase):
    def test_oauth_error_from_transport_uses_spotify_payload(self):
        error = TransportError(
            "HTTP status 400",
            status=400,
            data={"error": "invalid_grant", "error_description": "Refresh token revoked"},
        )

        caught = oauth_error_from_transport(error)

        self.assertIsInstance(caught, SpotifyAuthError)
        self.assertEqual(caught.args[0], "Spotify OAuth error: invalid_grant (Refresh token revoked)")

    def test_client_credentials_refresh_raises_spotify_auth_error(self):
        transport = FakeAuthTransport(
            error=TransportError(
                "HTTP status 400",
                status=400,
                data={"error": "invalid_client", "error_description": "Invalid client secret"},
            )
        )
        auth = ClientCredentialsAuth("client", "secret", transport=transport)

        with self.assertRaises(SpotifyAuthError) as caught:
            auth.refresh()

        self.assertIn("invalid_client", str(caught.exception))

    def test_authorization_code_refresh_raises_spotify_auth_error(self):
        transport = FakeAuthTransport(
            error=TransportError(
                "HTTP status 400",
                status=400,
                data={"error": "invalid_grant", "error_description": "Bad refresh token"},
            )
        )
        auth = AuthorizationCodeAuth(
            "client",
            "secret",
            "http://127.0.0.1:8080",
            refresh_token="refresh-123",
            transport=transport,
        )

        with self.assertRaises(SpotifyAuthError) as caught:
            auth.token()

        self.assertIn("invalid_grant", str(caught.exception))

    def test_token_cache_persists_redirect_uri_and_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tokens.json")
            cache = TokenCache(path)
            auth = AuthorizationCodeAuth(
                "client",
                "secret",
                "http://127.0.0.1:8080",
                scope=["user-read-email", "playlist-read-private"],
                refresh_token="refresh-123",
                token_cache=cache,
                transport=FakeAuthTransport(),
            )

            auth.token()
            saved = cache.load()

            self.assertEqual(saved["redirect_uri"], "http://127.0.0.1:8080")
            self.assertEqual(saved["scope"], "user-read-email playlist-read-private")


if __name__ == "__main__":
    unittest.main()
