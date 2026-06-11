import unittest

from spotapi.config import config_available


@unittest.skipUnless(
    config_available(),
    "Copy spotapi.local.json.example to spotapi.local.json and add credentials",
)
class SpotifyLiveTest(unittest.TestCase):
    def test_user_client_me(self):
        from spotapi import user_client

        client = user_client()
        user = client.me()

        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user.display_name)

    def test_app_client_track(self):
        from spotapi import app_client

        client = app_client()
        track = client.track("11dFghVXANMlKmJXsNCbNl", market="US")

        self.assertEqual(track.id, "11dFghVXANMlKmJXsNCbNl")
        self.assertIsNotNone(track.name)
        self.assertIsNotNone(track.album.name)
        self.assertIsNotNone(track.artists[0].name)


if __name__ == "__main__":
    unittest.main()
