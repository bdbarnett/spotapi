import unittest

from spotapi import Page, Playlist, PlaylistTrackPage, Track, User, set_client


class _FakeClient:
    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    def track(self, object_id):
        self.calls.append(("track", object_id))
        return Track(self._responses.get(("track", object_id), {}))


class SpotifyObjectHydrationTest(unittest.TestCase):
    def test_missing_field_hydrates_fetchable_object(self):
        client = _FakeClient(
            {
                ("track", "t1"): {
                    "id": "t1",
                    "name": "Full Track",
                    "type": "track",
                    "popularity": 77,
                },
            }
        )
        set_client(client)

        track = Track({"id": "t1", "name": "Stub", "type": "track"})
        self.assertFalse(track._fetched)
        self.assertEqual(track.popularity, 77)
        self.assertTrue(track._fetched)
        self.assertEqual(client.calls, [("track", "t1")])

    def test_present_field_does_not_hydrate(self):
        client = _FakeClient({})
        set_client(client)

        track = Track({"id": "t1", "name": "Stub", "type": "track"})
        self.assertEqual(track.name, "Stub")
        self.assertFalse(track._fetched)
        self.assertEqual(client.calls, [])

    def test_non_fetchable_object_does_not_mark_fetched(self):
        set_client(_FakeClient({}))

        user = User({"id": "u1", "display_name": "Stub", "type": "user"})
        self.assertIsNone(user.followers)
        self.assertFalse(user._fetched)

    def test_repr_does_not_hydrate(self):
        client = _FakeClient({("track", "t1"): {"id": "t1", "name": "Full", "type": "track"}})
        set_client(client)

        track = Track({"id": "t1", "type": "track"})
        repr(track)
        self.assertFalse(track._fetched)
        self.assertEqual(client.calls, [])

    def test_playlist_items_ref_uses_page_method(self):
        class _PlaylistClient(_FakeClient):
            def playlist(self, object_id):
                self.calls.append(("playlist", object_id))
                return Playlist(
                    {
                        "id": object_id,
                        "name": "Mine",
                        "items": {"href": "x", "total": 1},
                    }
                )

            def playlist_items(self, object_id):
                self.calls.append(("playlist_items", object_id))
                return PlaylistTrackPage(
                    {
                        "href": "items",
                        "limit": 1,
                        "next": None,
                        "offset": 0,
                        "previous": None,
                        "total": 1,
                        "items": [
                            {
                                "added_at": "2026-01-01T00:00:00Z",
                                "item": {"id": "t1", "name": "Song", "type": "track"},
                            }
                        ],
                    }
                )

        client = _PlaylistClient({})
        set_client(client)

        playlist = Playlist({"id": "pl1", "name": "Mine", "items": {"href": "x", "total": 1}})
        item = playlist.items[0]
        self.assertEqual(item.item.name, "Song")
        self.assertEqual(client.calls[0], ("playlist", "pl1"))
        self.assertEqual(client.calls[-1], ("playlist_items", "pl1"))

    def test_page_items_uses_peek(self):
        page = Page(
            {
                "href": "h",
                "limit": 1,
                "next": None,
                "offset": 0,
                "previous": None,
                "total": 1,
                "items": [{"id": "t1", "name": "Song", "type": "track"}],
            }
        )
        page._item_class = "Track"
        self.assertEqual(page[0].name, "Song")
        self.assertFalse(page._fetched)


if __name__ == "__main__":
    unittest.main()
