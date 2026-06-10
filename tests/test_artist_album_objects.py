import unittest

from spotapi import Album, Artist, set_client


class FakeClient:
    def __init__(self):
        self.calls = []

    def artist(self, object_id):
        self.calls.append(("artist", object_id))
        return Artist(
            {
                "id": object_id,
                "name": "Full Artist",
                "followers": {"href": None, "total": 123},
                "genres": ["rock", "pop"],
                "images": [
                    {"url": "https://image.example/artist-large.jpg", "height": 640, "width": 640},
                ],
                "popularity": 81,
            }
        )

    def album(self, object_id):
        self.calls.append(("album", object_id))
        return Album(
            {
                "id": object_id,
                "name": "Full Album",
                "copyrights": [
                    {"text": "2026 Example Records", "type": "C"},
                ],
                "external_ids": {"upc": "123456789012"},
                "genres": ["soundtrack"],
                "label": "Example Records",
                "popularity": 64,
                "tracks": {
                    "href": "https://api.spotify.com/v1/albums/album-1/tracks",
                    "limit": 20,
                    "next": None,
                    "offset": 0,
                    "previous": None,
                    "total": 1,
                    "items": [
                        {"id": "track-1", "name": "Album Track"},
                    ],
                },
            }
        )


class ArtistAlbumObjectTest(unittest.TestCase):
    def tearDown(self):
        set_client(None)

    def test_artist_full_fields_fetch_once(self):
        client = FakeClient()
        set_client(client)

        artist = Artist({"id": "artist-1", "name": "Simplified Artist"})

        self.assertEqual(artist.followers.total, 123)
        self.assertEqual(artist.genres, ["rock", "pop"])
        self.assertEqual(artist.images[0].url, "https://image.example/artist-large.jpg")
        self.assertEqual(artist.popularity, 81)
        self.assertEqual(client.calls, [("artist", "artist-1")])

    def test_album_wraps_simplified_fields_without_fetching(self):
        client = FakeClient()
        set_client(client)

        album = Album(
            {
                "id": "album-1",
                "name": "Simplified Album",
                "artists": [
                    {"id": "artist-1", "name": "Album Artist"},
                ],
                "images": [
                    {"url": "https://image.example/album.jpg", "height": 300, "width": 300},
                ],
            }
        )

        self.assertEqual(album.artists[0].name, "Album Artist")
        self.assertEqual(album.images[0].width, 300)
        self.assertEqual(client.calls, [])

    def test_album_full_fields_fetch_once(self):
        client = FakeClient()
        set_client(client)

        album = Album({"id": "album-1", "name": "Simplified Album"})

        self.assertEqual(album.copyrights[0].text, "2026 Example Records")
        self.assertEqual(album.external_ids.upc, "123456789012")
        self.assertEqual(album.tracks.items[0].name, "Album Track")
        self.assertEqual(album.popularity, 64)
        self.assertEqual(client.calls, [("album", "album-1")])


if __name__ == "__main__":
    unittest.main()
