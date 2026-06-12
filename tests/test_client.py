import unittest

from spotapi import SpotifyClient
from spotapi.auth import ClientCredentialsAuth
from spotapi.transport import TransportError


class _CountingAuth(ClientCredentialsAuth):
    def __init__(self):
        super().__init__("client-id", "client-secret")
        self.access_token = "token-1"
        self.expires_at = 9999999999
        self.refresh_count = 0

    def refresh(self):
        self.refresh_count += 1
        self.access_token = "token-{}".format(self.refresh_count + 1)
        self.expires_at = 9999999999
        return self.access_token


class SpotifyClientRetryTest(unittest.TestCase):
    def test_retries_once_after_401_when_auth_is_available(self):
        import spotapi.client as client_module

        auth = _CountingAuth()
        client = SpotifyClient(auth=auth, auto_set=False)
        calls = []

        def fake_get_json(path, access_token=None, query=None):
            calls.append(access_token)
            if access_token == "token-1":
                raise TransportError("HTTP status 401", 401, None)
            return {"id": "me", "display_name": "User", "type": "user"}

        original = client_module.get_json
        client_module.get_json = fake_get_json
        try:
            user = client.me()
        finally:
            client_module.get_json = original

        self.assertEqual(user.display_name, "User")
        self.assertEqual(calls, ["token-1", "token-2"])
        self.assertEqual(auth.refresh_count, 1)

    def test_does_not_retry_401_without_auth(self):
        import spotapi.client as client_module

        client = SpotifyClient(access_token="static-token", auto_set=False)

        def fake_get_json(path, access_token=None, query=None):
            raise TransportError("HTTP status 401", 401, None)

        original = client_module.get_json
        client_module.get_json = fake_get_json
        try:
            with self.assertRaises(TransportError) as context:
                client.me()
        finally:
            client_module.get_json = original

        self.assertEqual(context.exception.status, 401)


if __name__ == "__main__":
    unittest.main()
