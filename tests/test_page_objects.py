import unittest

from spotapi import Page, TrackPage


class PageObjectTest(unittest.TestCase):
    def test_track_page_wraps_items(self):
        page = TrackPage(
            {
                "href": "https://api.spotify.com/v1/albums/album-1/tracks",
                "limit": 2,
                "next": None,
                "offset": 0,
                "previous": None,
                "total": 2,
                "items": [
                    {"id": "track-1", "name": "First Track"},
                    {"id": "track-2", "name": "Second Track"},
                ],
            }
        )

        self.assertIsInstance(page, Page)
        self.assertEqual(page.limit, 2)
        self.assertEqual(page.total, 2)
        self.assertEqual([track.name for track in page.items], ["First Track", "Second Track"])

    def test_page_can_be_iterated(self):
        page = TrackPage(
            {
                "items": [
                    {"id": "track-1", "name": "First Track"},
                    {"id": "track-2", "name": "Second Track"},
                ],
            }
        )

        self.assertEqual(len(page), 2)
        self.assertEqual([track.id for track in page], ["track-1", "track-2"])

    def test_missing_page_items_return_empty_tuple(self):
        page = TrackPage({})

        self.assertEqual(page.items, ())
        self.assertEqual(len(page), 0)


if __name__ == "__main__":
    unittest.main()
