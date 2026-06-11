import os
import unittest


def live_tests_enabled():
    if os.environ.get("SPOTIFY_LIVE") != "1":
        return False

    if not os.environ.get("SPOTIFY_CLIENT_ID"):
        return False

    if not os.environ.get("SPOTIFY_CLIENT_SECRET"):
        return False

    if os.environ.get("SPOTIFY_REFRESH_TOKEN"):
        return True

    token_cache = os.environ.get("SPOTIFY_TOKEN_CACHE", "tokens.json")
    if os.path.isfile(token_cache):
        return True

    return False


@unittest.skipUnless(live_tests_enabled(), "Set SPOTIFY_LIVE=1 with OAuth credentials and a refresh token or token cache")
class LiveOAuthTest(unittest.TestCase):
    def test_refresh_token_and_me(self):
        from spotapi import user_client_from_env

        client = user_client_from_env()
        user = client.me()

        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user.display_name)


@unittest.skipUnless(live_tests_enabled(), "Set SPOTIFY_LIVE=1 with OAuth credentials and a refresh token or token cache")
class LiveClientCredentialsTest(unittest.TestCase):
    def test_client_credentials_track(self):
        from spotapi import SpotifyClient

        client = SpotifyClient(
            client_id=os.environ["SPOTIFY_CLIENT_ID"],
            client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        )
        track = client.track("11dFghVXANMlKmJXsNCbNl", market="US")

        self.assertEqual(track.id, "11dFghVXANMlKmJXsNCbNl")
        self.assertIsNotNone(track.name)
        self.assertIsNotNone(track.album.name)
        self.assertIsNotNone(track.artists[0].name)


if __name__ == "__main__":
    unittest.main()
