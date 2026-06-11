import unittest

from spotapi import config_available


@unittest.skipUnless(
    config_available(),
    "Copy spotapi.local.json.example to spotapi.local.json and add credentials",
)
class SpotifyLiveTest(unittest.TestCase):
    def test_spotify_client_me(self):
        from spotapi import SpotifyClient

        client = SpotifyClient()
        user = client.me()

        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user.display_name)

    def test_spotify_client_track_with_client_credentials(self):
        from spotapi import SpotifyClient, credentials_from_config, load_config

        config = load_config()
        client_id, client_secret = credentials_from_config(config)
        client = SpotifyClient(client_id=client_id, client_secret=client_secret)
        track = client.track("11dFghVXANMlKmJXsNCbNl", market="US")

        self.assertEqual(track.id, "11dFghVXANMlKmJXsNCbNl")
        self.assertIsNotNone(track.name)
        self.assertIsNotNone(track.album.name)
        self.assertIsNotNone(track.artists[0].name)


if __name__ == "__main__":
    unittest.main()
