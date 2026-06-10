import os
import tempfile
import unittest

from spotapi import (
    AuthorizationCodeAuth,
    ClientCredentialsAuth,
    SpotifyAuthError,
    SpotifyClient,
    TokenCache,
    Track,
    authorization_url,
    code_challenge_s256,
    generate_code_verifier,
    parse_callback_url,
    pkce_pair,
)
from spotapi.auth import basic_token
from spotapi.transport import TransportError, build_url, put_body, put_json, query_string, response_json, unquote_plus


class FakeAuthTransport:
    def __init__(self):
        self.calls = []

    def post_form_json(self, url, body, headers):
        self.calls.append((url, body, headers))
        return {
            "access_token": "token-from-auth",
            "expires_in": 3600,
        }


class FakeApiTransport:
    def __init__(self):
        self.calls = []

    def get_json(self, url, headers):
        self.calls.append((url, headers))
        return {
            "id": "track-1",
            "name": "Authed Track",
        }


class FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self.data = data
        self.closed = False

    def json(self):
        return self.data

    def close(self):
        self.closed = True


class FakeDeinitResponse:
    def __init__(self, status, data):
        self.status_code = status
        self.data = data
        self.deinitialized = False

    def json(self):
        return self.data

    def deinit(self):
        self.deinitialized = True


class FakeWriteTransport:
    def __init__(self):
        self.calls = []

    def put(self, url, data=None, headers=None):
        self.calls.append((url, data, headers))
        return FakeResponse(204, None)


class AuthTransportTest(unittest.TestCase):
    def test_basic_token(self):
        self.assertEqual(basic_token("client", "secret"), "Y2xpZW50OnNlY3JldA==")

    def test_authorization_url_encodes_oauth_query(self):
        url = authorization_url(
            "client",
            "http://localhost:8888/callback",
            scope=["user-read-email", "playlist-read-private"],
            state="state value",
            show_dialog=True,
        )

        self.assertEqual(
            url,
            "https://accounts.spotify.com/authorize?"
            "response_type=code&client_id=client&redirect_uri=http%3A%2F%2Flocalhost%3A8888%2Fcallback&"
            "scope=user-read-email%20playlist-read-private&state=state%20value&show_dialog=true",
        )

    def test_authorization_url_adds_pkce_challenge_from_verifier(self):
        auth = AuthorizationCodeAuth(
            "client",
            "secret",
            "http://localhost:8888/callback",
            code_verifier="dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
        )

        url = auth.authorize_url()

        self.assertEqual(
            url,
            "https://accounts.spotify.com/authorize?"
            "response_type=code&client_id=client&redirect_uri=http%3A%2F%2Flocalhost%3A8888%2Fcallback&"
            "code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256",
        )

    def test_pkce_challenge_uses_s256(self):
        self.assertEqual(
            code_challenge_s256("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"),
            "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        )

    def test_generate_code_verifier_length(self):
        verifier = generate_code_verifier(43)

        self.assertEqual(len(verifier), 43)

    def test_generate_code_verifier_rejects_invalid_lengths(self):
        with self.assertRaises(SpotifyAuthError):
            generate_code_verifier(42)

        with self.assertRaises(SpotifyAuthError):
            generate_code_verifier(129)

    def test_pkce_pair_returns_verifier_and_challenge(self):
        verifier, challenge = pkce_pair(43)

        self.assertEqual(len(verifier), 43)
        self.assertEqual(challenge, code_challenge_s256(verifier))

    def test_parse_callback_url_decodes_query_values(self):
        values = parse_callback_url("http://localhost:8888/callback?code=abc%20123&state=state+value#ignored")

        self.assertEqual(values, {"code": "abc 123", "state": "state value"})

    def test_auth_refresh_posts_client_credentials_form(self):
        transport = FakeAuthTransport()
        auth = ClientCredentialsAuth("client", "secret", transport=transport)

        token = auth.token()

        self.assertEqual(token, "token-from-auth")
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(transport.calls[0][0], "https://accounts.spotify.com/api/token")
        self.assertEqual(transport.calls[0][1], "grant_type=client_credentials")
        self.assertEqual(
            transport.calls[0][2],
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Basic Y2xpZW50OnNlY3JldA==",
            },
        )

    def test_client_credentials_auth_is_used_by_client(self):
        auth_transport = FakeAuthTransport()
        api_transport = FakeApiTransport()
        auth = ClientCredentialsAuth("client", "secret", transport=auth_transport)
        client = SpotifyClient(auth=auth, transport=api_transport, auto_set=False)

        track = client.track("track-1")

        self.assertIsInstance(track, Track)
        self.assertEqual(track.name, "Authed Track")
        self.assertEqual(
            api_transport.calls,
            [
                (
                    "https://api.spotify.com/v1/tracks/track-1",
                    {"Authorization": "Bearer token-from-auth"},
                ),
            ],
        )
        self.assertEqual(len(auth_transport.calls), 1)

    def test_client_id_secret_build_auth_object(self):
        api_transport = FakeApiTransport()
        client = SpotifyClient(
            client_id="client",
            client_secret="secret",
            transport=api_transport,
            auto_set=False,
        )

        self.assertIsInstance(client.auth, ClientCredentialsAuth)

    def test_authorization_code_exchange_posts_code_form(self):
        transport = FakeAuthTransport()
        auth = AuthorizationCodeAuth(
            "client",
            "secret",
            "http://localhost:8888/callback",
            code_verifier="verifier",
            transport=transport,
        )

        token = auth.exchange_code("code-123")

        self.assertEqual(token, "token-from-auth")
        self.assertEqual(auth.access_token, "token-from-auth")
        self.assertEqual(
            transport.calls,
            [
                (
                    "https://accounts.spotify.com/api/token",
                    "grant_type=authorization_code&code=code-123&redirect_uri=http%3A%2F%2Flocalhost%3A8888%2Fcallback&"
                    "code_verifier=verifier",
                    {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": "Basic Y2xpZW50OnNlY3JldA==",
                    },
                ),
            ],
        )

    def test_authorization_code_exchange_callback_url_validates_state(self):
        transport = FakeAuthTransport()
        auth = AuthorizationCodeAuth(
            "client",
            "secret",
            "http://localhost:8888/callback",
            transport=transport,
        )

        token = auth.exchange_callback_url(
            "http://localhost:8888/callback?code=code-123&state=expected",
            expected_state="expected",
        )

        self.assertEqual(token, "token-from-auth")
        self.assertEqual(
            transport.calls[0][1],
            "grant_type=authorization_code&code=code-123&redirect_uri=http%3A%2F%2Flocalhost%3A8888%2Fcallback",
        )

    def test_authorization_code_exchange_callback_url_rejects_state_mismatch(self):
        auth = AuthorizationCodeAuth("client", "secret", "http://localhost:8888/callback")

        with self.assertRaises(SpotifyAuthError):
            auth.exchange_callback_url(
                "http://localhost:8888/callback?code=code-123&state=actual",
                expected_state="expected",
            )

    def test_authorization_code_exchange_callback_url_rejects_callback_error(self):
        auth = AuthorizationCodeAuth("client", "secret", "http://localhost:8888/callback")

        with self.assertRaises(SpotifyAuthError):
            auth.exchange_callback_url("http://localhost:8888/callback?error=access_denied")

    def test_authorization_code_refresh_posts_refresh_token_form(self):
        transport = FakeAuthTransport()
        auth = AuthorizationCodeAuth(
            "client",
            "secret",
            "http://localhost:8888/callback",
            refresh_token="refresh-123",
            transport=transport,
        )

        token = auth.token()

        self.assertEqual(token, "token-from-auth")
        self.assertEqual(
            transport.calls,
            [
                (
                    "https://accounts.spotify.com/api/token",
                    "grant_type=refresh_token&refresh_token=refresh-123",
                    {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": "Basic Y2xpZW50OnNlY3JldA==",
                    },
                ),
            ],
        )

    def test_authorization_code_auth_loads_and_saves_token_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tokens.json")
            cache = TokenCache(path)
            cache.save(
                {
                    "access_token": "cached-token",
                    "expires_at": 0,
                    "refresh_token": "cached-refresh",
                }
            )
            transport = FakeAuthTransport()
            auth = AuthorizationCodeAuth(
                "client",
                "secret",
                "http://localhost:8888/callback",
                token_cache=cache,
                transport=transport,
            )

            token = auth.token()
            saved = cache.load()

            self.assertEqual(token, "token-from-auth")
            self.assertEqual(saved["access_token"], "token-from-auth")
            self.assertEqual(saved["refresh_token"], "cached-refresh")

    def test_authorization_code_token_requires_refresh_token_or_code(self):
        auth = AuthorizationCodeAuth("client", "secret", "http://localhost:8888/callback")

        with self.assertRaises(SpotifyAuthError):
            auth.token()

    def test_transport_query_helpers(self):
        self.assertEqual(query_string({"fields": "id,name", "market": "US"}), "fields=id%2Cname&market=US")
        self.assertEqual(unquote_plus("hello+world%21"), "hello world!")
        self.assertEqual(
            build_url("/tracks/track-1", {"market": "US"}),
            "https://api.spotify.com/v1/tracks/track-1?market=US",
        )
        self.assertEqual(
            build_url("https://api.spotify.com/v1/me/tracks", {"limit": 1}),
            "https://api.spotify.com/v1/me/tracks?limit=1",
        )

    def test_put_json_sends_json_body_and_accepts_no_content(self):
        transport = FakeWriteTransport()

        data = put_json("/me/tracks", {"ids": ["track-1"]}, access_token="token", transport=transport)

        self.assertIsNone(data)
        self.assertEqual(
            transport.calls,
            [
                (
                    "https://api.spotify.com/v1/me/tracks",
                    '{"ids": ["track-1"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
            ],
        )

    def test_put_body_sends_raw_body_and_content_type(self):
        transport = FakeWriteTransport()

        data = put_body("/playlists/playlist-1/images", "base64data", "image/jpeg", access_token="token", transport=transport)

        self.assertIsNone(data)
        self.assertEqual(
            transport.calls,
            [
                (
                    "https://api.spotify.com/v1/playlists/playlist-1/images",
                    "base64data",
                    {
                        "Content-Type": "image/jpeg",
                        "Authorization": "Bearer token",
                    },
                ),
            ],
        )

    def test_response_json_closes_success_response(self):
        response = FakeResponse(200, {"ok": True})

        data = response_json(response)

        self.assertEqual(data, {"ok": True})
        self.assertEqual(response.closed, True)

    def test_response_json_deinitializes_circuitpython_style_response(self):
        response = FakeDeinitResponse(200, {"ok": True})

        data = response_json(response)

        self.assertEqual(data, {"ok": True})
        self.assertEqual(response.deinitialized, True)

    def test_response_json_returns_none_for_no_content(self):
        response = FakeResponse(204, None)

        data = response_json(response)

        self.assertIsNone(data)
        self.assertEqual(response.closed, True)

    def test_response_json_raises_transport_error_for_http_error(self):
        response = FakeResponse(401, {"error": {"message": "Bad token"}})

        with self.assertRaises(TransportError) as caught:
            response_json(response)

        self.assertEqual(caught.exception.status, 401)
        self.assertEqual(caught.exception.data, {"error": {"message": "Bad token"}})
        self.assertEqual(response.closed, True)


if __name__ == "__main__":
    unittest.main()
