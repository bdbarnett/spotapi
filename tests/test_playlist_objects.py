import unittest

from spotapi import Episode, Playlist, PlaylistTrackPage, Track, set_client


class FakeClient:
    def __init__(self):
        self.calls = []

    def playlist(self, object_id):
        self.calls.append(("playlist", object_id))
        return Playlist(
            {
                "id": object_id,
                "name": "Full Playlist",
                "tracks": {
                    "href": "https://api.spotify.com/v1/playlists/playlist-1/tracks",
                    "limit": 20,
                    "next": None,
                    "offset": 0,
                    "previous": None,
                    "total": 2,
                    "items": [
                        {
                            "added_at": "2026-06-04T01:02:03Z",
                            "added_by": {"id": "user-1", "display_name": "Adder"},
                            "is_local": False,
                            "item": {"id": "track-1", "name": "Playlist Track", "type": "track"},
                        },
                        {
                            "added_at": "2026-06-04T01:03:04Z",
                            "added_by": {"id": "user-2", "display_name": "Adder Two"},
                            "is_local": False,
                            "item": {"id": "episode-1", "name": "Playlist Episode", "type": "episode"},
                        },
                    ],
                },
            }
        )


class PlaylistObjectTest(unittest.TestCase):
    def tearDown(self):
        set_client(None)

    def test_playlist_wraps_simple_nested_fields(self):
        playlist = Playlist(
            {
                "id": "playlist-1",
                "name": "Simplified Playlist",
                "owner": {"id": "owner-1", "display_name": "Owner"},
                "images": [
                    {"url": "https://image.example/playlist.jpg", "height": 300, "width": 300},
                ],
            }
        )

        self.assertEqual(playlist.owner.display_name, "Owner")
        self.assertEqual(playlist.images[0].url, "https://image.example/playlist.jpg")

    def test_playlist_tracks_ref_hydrates_to_track_page(self):
        client = FakeClient()
        set_client(client)

        playlist = Playlist(
            {
                "id": "playlist-1",
                "name": "Simplified Playlist",
                "tracks": {
                    "href": "https://api.spotify.com/v1/playlists/playlist-1/tracks",
                    "total": 2,
                },
            }
        )

        self.assertIsInstance(playlist.tracks, PlaylistTrackPage)
        self.assertEqual(playlist.tracks.total, 2)
        self.assertEqual(playlist.tracks.items[0].item.name, "Playlist Track")
        self.assertEqual(client.calls, [("playlist", "playlist-1")])

    def test_playlist_track_items_are_typed(self):
        page = PlaylistTrackPage(
            {
                "items": [
                    {
                        "item": {"id": "track-1", "name": "Playlist Track", "type": "track"},
                    },
                    {
                        "item": {"id": "episode-1", "name": "Playlist Episode", "type": "episode"},
                    },
                ],
            }
        )

        self.assertIsInstance(page.items[0].item, Track)
        self.assertIsInstance(page.items[1].item, Episode)


if __name__ == "__main__":
    unittest.main()
