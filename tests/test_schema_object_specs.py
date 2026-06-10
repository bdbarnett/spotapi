import unittest

import spotapi
from spotapi import (
    AudioAnalysis,
    Audiobook,
    Category,
    CurrentlyPlaying,
    PrivateUser,
    Queue,
    Recommendations,
    SPOTIFY_OBJECT_SPECS,
    SpotifyObject,
)


class SchemaObjectSpecsTest(unittest.TestCase):
    def test_every_declared_spec_is_exported(self):
        for spec in SPOTIFY_OBJECT_SPECS:
            cls = getattr(spotapi, spec["name"])
            self.assertTrue(issubclass(cls, SpotifyObject))

    def test_audio_analysis_wraps_nested_intervals(self):
        analysis = AudioAnalysis(
            {
                "bars": [
                    {"start": 0.0, "duration": 1.0, "confidence": 0.9},
                ],
                "sections": [
                    {"start": 0.0, "duration": 8.0, "tempo": 120.0},
                ],
            }
        )

        self.assertEqual(analysis.bars[0].confidence, 0.9)
        self.assertEqual(analysis.sections[0].tempo, 120.0)

    def test_recommendations_wrap_tracks_and_seeds(self):
        recommendations = Recommendations(
            {
                "seeds": [
                    {"id": "artist-1", "type": "artist", "initialPoolSize": 100},
                ],
                "tracks": [
                    {"id": "track-1", "name": "Recommended Track"},
                ],
            }
        )

        self.assertEqual(recommendations.seeds[0].initialPoolSize, 100)
        self.assertEqual(recommendations.tracks[0].name, "Recommended Track")

    def test_queue_and_currently_playing_wrap_typed_items(self):
        queue = Queue(
            {
                "currently_playing": {"id": "track-1", "type": "track"},
                "queue": [
                    {"id": "episode-1", "type": "episode"},
                ],
            }
        )
        currently_playing = CurrentlyPlaying(
            {
                "item": {"id": "track-2", "type": "track"},
                "actions": {"pausing": True},
            }
        )

        self.assertEqual(queue.currently_playing.id, "track-1")
        self.assertEqual(queue.queue[0].id, "episode-1")
        self.assertEqual(currently_playing.actions.pausing, True)

    def test_private_user_category_and_audiobook_helpers(self):
        user = PrivateUser(
            {
                "id": "user-1",
                "explicit_content": {"filter_enabled": True},
            }
        )
        category = Category(
            {
                "id": "category-1",
                "icons": [
                    {"url": "https://image.example/category.jpg"},
                ],
            }
        )
        audiobook = Audiobook(
            {
                "id": "audiobook-1",
                "authors": [{"name": "Author One"}],
                "narrators": [{"name": "Narrator One"}],
            }
        )

        self.assertEqual(user.explicit_content.filter_enabled, True)
        self.assertEqual(category.icons[0].url, "https://image.example/category.jpg")
        self.assertEqual(audiobook.authors[0].name, "Author One")
        self.assertEqual(audiobook.narrators[0].name, "Narrator One")


if __name__ == "__main__":
    unittest.main()
