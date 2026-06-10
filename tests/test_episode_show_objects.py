import unittest

from spotapi import Episode, EpisodePage, Show, set_client


class FakeClient:
    def __init__(self):
        self.calls = []

    def episode(self, object_id):
        self.calls.append(("episode", object_id))
        return Episode(
            {
                "id": object_id,
                "name": "Full Episode",
                "show": {
                    "id": "show-1",
                    "name": "Simplified Show",
                    "type": "show",
                },
            }
        )

    def show(self, object_id):
        self.calls.append(("show", object_id))
        return Show(
            {
                "id": object_id,
                "name": "Full Show",
                "episodes": {
                    "href": "https://api.spotify.com/v1/shows/show-1/episodes",
                    "limit": 20,
                    "next": None,
                    "offset": 0,
                    "previous": None,
                    "total": 1,
                    "items": [
                        {
                            "id": "episode-1",
                            "name": "Show Episode",
                            "type": "episode",
                        },
                    ],
                },
            }
        )


class EpisodeShowObjectTest(unittest.TestCase):
    def tearDown(self):
        set_client(None)

    def test_episode_wraps_base_fields_without_fetching(self):
        client = FakeClient()
        set_client(client)

        episode = Episode(
            {
                "id": "episode-1",
                "name": "Simplified Episode",
                "languages": ["en"],
                "images": [
                    {"url": "https://image.example/episode.jpg", "height": 300, "width": 300},
                ],
                "resume_point": {"fully_played": False, "resume_position_ms": 1000},
            }
        )

        self.assertEqual(episode.languages, ["en"])
        self.assertEqual(episode.images[0].height, 300)
        self.assertEqual(episode.resume_point.resume_position_ms, 1000)
        self.assertEqual(client.calls, [])

    def test_episode_show_fetches_once(self):
        client = FakeClient()
        set_client(client)

        episode = Episode({"id": "episode-1", "name": "Simplified Episode"})

        self.assertEqual(episode.show.name, "Simplified Show")
        self.assertEqual(episode.show.type, "show")
        self.assertEqual(client.calls, [("episode", "episode-1")])

    def test_show_episodes_fetch_once(self):
        client = FakeClient()
        set_client(client)

        show = Show({"id": "show-1", "name": "Simplified Show"})

        self.assertIsInstance(show.episodes, EpisodePage)
        self.assertEqual(show.episodes.items[0].name, "Show Episode")
        self.assertEqual(client.calls, [("show", "show-1")])


if __name__ == "__main__":
    unittest.main()
