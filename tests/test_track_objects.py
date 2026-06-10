import unittest

from spotapi import Track, get_client, set_client


class FakeClient:
    def __init__(self):
        self.calls = []

    def track(self, object_id):
        self.calls.append(object_id)
        return Track(
            {
                "id": object_id,
                "name": "Full Track",
                "album": {"id": "album-1", "name": "Full Album"},
                "external_ids": {"isrc": "USRC17607839"},
                "popularity": 72,
            }
        )


class TrackObjectTest(unittest.TestCase):
    def tearDown(self):
        set_client(None)

    def test_simplified_track_wraps_nested_artists_without_fetching(self):
        client = FakeClient()
        set_client(client)

        track = Track(
            {
                "id": "track-1",
                "name": "Simplified Track",
                "artists": [
                    {"id": "artist-1", "name": "First Artist"},
                    {"id": "artist-2", "name": "Second Artist"},
                ],
            }
        )

        self.assertEqual(track.name, "Simplified Track")
        self.assertEqual(
            [artist.name for artist in track.artists],
            ["First Artist", "Second Artist"],
        )
        self.assertEqual(track.artists[0].external_urls, None)
        self.assertEqual(client.calls, [])

    def test_full_track_fields_fetch_once(self):
        client = FakeClient()
        set_client(client)

        track = Track({"id": "track-1", "name": "Simplified Track"})

        self.assertEqual(track.album.name, "Full Album")
        self.assertEqual(track.popularity, 72)
        self.assertEqual(track.external_ids.isrc, "USRC17607839")
        self.assertEqual(client.calls, ["track-1"])

    def test_external_urls_are_a_single_object(self):
        track = Track(
            {
                "id": "track-1",
                "external_urls": {
                    "spotify": "https://open.spotify.com/track/track-1",
                },
            }
        )

        self.assertEqual(
            track.external_urls.spotify,
            "https://open.spotify.com/track/track-1",
        )
        self.assertFalse(hasattr(track, "spotify_url"))

    def test_present_none_does_not_fetch(self):
        client = FakeClient()
        set_client(client)

        track = Track({"id": "track-1", "preview_url": None})

        self.assertIsNone(track.get("preview_url"))
        self.assertEqual(client.calls, [])

    def test_missing_client_marks_object_as_fetched(self):
        track = Track({"id": "track-1"})

        self.assertIsNone(track.album)
        self.assertIsNone(track.popularity)
        self.assertIsNone(get_client())


if __name__ == "__main__":
    unittest.main()
