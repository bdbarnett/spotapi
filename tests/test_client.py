import unittest

from spotapi import (
    Album,
    AlbumPage,
    ArtistCursorPage,
    ArtistPage,
    CategoryPage,
    CurrentlyPlaying,
    Device,
    Image,
    Playlist,
    PlaylistPage,
    PlaylistTrackPage,
    PlayHistoryCursorPage,
    Recommendations,
    SavedAlbumPage,
    SavedEpisodePage,
    SavedShowPage,
    SavedTrackPage,
    SearchResults,
    SnapshotResult,
    SpotifyClient,
    SpotifyClientError,
    Track,
    TrackPage,
    get_client,
    set_client,
    snapshot_id,
)


class FakeSpotifyClient(SpotifyClient):
    def __init__(self):
        self.calls = []
        SpotifyClient.__init__(self, access_token="token")

    def _get_json(self, path, query=None):
        self.calls.append((path, query))

        if path == "/tracks/track-1":
            return {
                "id": "track-1",
                "name": "Fetched Track",
                "album": {"id": "album-1", "name": "Fetched Album"},
            }
        if path == "/albums/album-1":
            return {"id": "album-1", "name": "Fetched Album"}
        if path == "/playlists/playlist-1":
            return {"id": "playlist-1", "name": "Fetched Playlist"}
        if path == "/tracks":
            return {
                "tracks": [
                    {"id": "track-1", "name": "First Track"},
                    {"id": "track-2", "name": "Second Track"},
                ],
            }
        if path == "/albums/album-1/tracks":
            return {
                "items": [
                    {"id": "track-1", "name": "Album Track"},
                ],
                "limit": 1,
                "offset": 0,
                "next": "https://api.spotify.com/v1/albums/album-1/tracks?offset=1&limit=1",
                "previous": None,
                "total": 1,
            }
        if path == "https://api.spotify.com/v1/albums/album-1/tracks?offset=1&limit=1":
            return {
                "items": [
                    {"id": "track-2", "name": "Next Album Track"},
                ],
                "limit": 1,
                "offset": 1,
                "next": None,
                "previous": "https://api.spotify.com/v1/albums/album-1/tracks?offset=0&limit=1",
                "total": 2,
            }
        if path == "https://api.spotify.com/v1/albums/album-1/tracks?offset=0&limit=1":
            return {
                "items": [
                    {"id": "track-1", "name": "Previous Album Track"},
                ],
                "limit": 1,
                "offset": 0,
                "next": "https://api.spotify.com/v1/albums/album-1/tracks?offset=1&limit=1",
                "previous": None,
                "total": 2,
            }
        if path == "/artists/artist-1/top-tracks":
            return {
                "tracks": [
                    {"id": "track-1", "name": "Artist Top Track"},
                ],
            }
        if path == "/artists/artist-1/related-artists":
            return {
                "artists": [
                    {"id": "artist-2", "name": "Related Artist"},
                ],
            }
        if path == "/browse/categories/pop/playlists":
            return {
                "playlists": {
                    "items": [{"id": "playlist-1", "name": "Category Playlist"}],
                    "total": 1,
                },
            }
        if path == "/playlists/playlist-1/tracks":
            return {
                "items": [
                    {
                        "item": {"id": "track-1", "name": "Playlist Track", "type": "track"},
                    },
                ],
                "limit": 1,
                "offset": 0,
                "total": 1,
            }
        if path == "/playlists/playlist-1/items":
            return {
                "items": [
                    {
                        "item": {"id": "track-1", "name": "Playlist Item", "type": "track"},
                    },
                ],
                "limit": 1,
                "offset": 0,
                "total": 1,
            }
        if path == "/audio-features/track-1":
            return {"id": "track-1", "danceability": 0.8}
        if path == "/recommendations":
            return {
                "seeds": [{"id": "artist-1", "type": "artist"}],
                "tracks": [{"id": "track-1", "name": "Recommended Track"}],
            }
        if path == "/browse/categories":
            return {
                "categories": {
                    "items": [{"id": "pop", "name": "Pop"}],
                    "total": 1,
                },
            }
        if path == "/browse/new-releases":
            return {
                "albums": {
                    "items": [{"id": "album-1", "name": "New Album"}],
                    "total": 1,
                },
            }
        if path == "/search":
            return {
                "tracks": {
                    "items": [{"id": "track-1", "name": "Search Track"}],
                    "total": 1,
                },
                "artists": {
                    "items": [{"id": "artist-1", "name": "Search Artist"}],
                    "total": 1,
                },
            }
        if path == "/me/player":
            return {
                "is_playing": True,
                "item": {"id": "track-1", "type": "track", "name": "Current Track"},
            }
        if path == "/me/player/devices":
            return {
                "devices": [
                    {"id": "device-1", "name": "Desktop", "type": "Computer"},
                ],
            }
        if path == "/me/player/recently-played":
            return {
                "items": [
                    {
                        "track": {"id": "track-1", "name": "Recent Track"},
                        "played_at": "2026-01-01T00:00:00Z",
                    },
                ],
                "cursors": {"after": "after-1", "before": "before-1"},
            }
        if path == "/me/playlists":
            return {
                "items": [{"id": "playlist-1", "name": "Current User Playlist"}],
                "total": 1,
            }
        if path == "/users/user-1/playlists":
            return {
                "items": [{"id": "playlist-1", "name": "Public User Playlist"}],
                "total": 1,
            }
        if path == "/me/albums":
            return {
                "items": [{"added_at": "2026-01-01T00:00:00Z", "album": {"id": "album-1", "name": "Saved Album"}}],
                "total": 1,
            }
        if path == "/me/tracks":
            return {
                "items": [{"added_at": "2026-01-01T00:00:00Z", "track": {"id": "track-1", "name": "Saved Track"}}],
                "total": 1,
            }
        if path == "/me/episodes":
            return {
                "items": [
                    {"added_at": "2026-01-01T00:00:00Z", "episode": {"id": "episode-1", "name": "Saved Episode"}}
                ],
                "total": 1,
            }
        if path == "/me/shows":
            return {
                "items": [{"added_at": "2026-01-01T00:00:00Z", "show": {"id": "show-1", "name": "Saved Show"}}],
                "total": 1,
            }
        if path == "/me/audiobooks":
            return {
                "items": [{"id": "audiobook-1", "name": "Saved Audiobook"}],
                "total": 1,
            }
        if path in (
            "/me/albums/contains",
            "/me/tracks/contains",
            "/me/episodes/contains",
            "/me/shows/contains",
            "/me/audiobooks/contains",
            "/me/library/contains",
            "/me/following/contains",
            "/playlists/playlist-1/followers/contains",
        ):
            return [True, False]
        if path == "/me/following":
            return {
                "artists": {
                    "items": [{"id": "artist-1", "name": "Followed Artist"}],
                    "cursors": {"after": "artist-1"},
                },
            }
        if path == "/me/top/artists":
            return {
                "items": [{"id": "artist-1", "name": "Top Artist"}],
                "total": 1,
            }
        if path == "/me/top/tracks":
            return {
                "items": [{"id": "track-1", "name": "Top Track"}],
                "total": 1,
            }
        if path == "/playlists/playlist-1/images":
            return [{"url": "https://example.com/cover.jpg", "height": 640, "width": 640}]
        if path == "/markets":
            return {"markets": ["US", "GB"]}
        if path == "/recommendations/available-genre-seeds":
            return {"genres": ["pop", "rock"]}

        return {"id": path.rsplit("/", 1)[-1]}


class FakeWriteTransport:
    def __init__(self):
        self.calls = []

    def request_json(self, method, url, body, headers):
        self.calls.append((method, url, body, headers))
        if url.endswith("/me/playlists") and method == "POST":
            return {"id": "playlist-1", "name": "Created Playlist"}
        if url.endswith("/users/user-1/playlists") and method == "POST":
            return {"id": "playlist-1", "name": "Created Playlist"}
        if "/playlists/" in url and url.endswith("/items") and method in ("POST", "DELETE"):
            return {"snapshot_id": "snapshot-1"}
        if "/playlists/" in url and url.endswith("/items") and method == "PUT":
            return {"snapshot_id": "snapshot-2"}
        if "/playlists/" in url and url.endswith("/tracks") and method in ("POST", "DELETE"):
            return {"snapshot_id": "snapshot-1"}
        if "/playlists/" in url and url.endswith("/tracks") and method == "PUT":
            return {"snapshot_id": "snapshot-2"}
        return None

    def request_body(self, method, url, body, headers):
        self.calls.append((method, url, body, headers))
        return None


class SpotifyClientTest(unittest.TestCase):
    def tearDown(self):
        set_client(None)

    def test_client_sets_current_client_by_default(self):
        client = FakeSpotifyClient()

        self.assertIs(get_client(), client)

    def test_snapshot_id_extracts_playlist_snapshot_id(self):
        result = SnapshotResult({"snapshot_id": "snapshot-1"})

        self.assertEqual(result.snapshot_id, "snapshot-1")
        self.assertEqual(snapshot_id(result), "snapshot-1")
        self.assertEqual(snapshot_id({"snapshot_id": "snapshot-1"}), "snapshot-1")
        self.assertIsNone(snapshot_id(None))

    def test_track_returns_track_object(self):
        client = FakeSpotifyClient()

        track = client.track("track-1", market="US")

        self.assertIsInstance(track, Track)
        self.assertEqual(track.name, "Fetched Track")
        self.assertEqual(client.calls, [("/tracks/track-1", {"market": "US"})])

    def test_album_returns_album_object(self):
        client = FakeSpotifyClient()

        album = client.album("album-1")

        self.assertIsInstance(album, Album)
        self.assertEqual(album.name, "Fetched Album")
        self.assertEqual(client.calls, [("/albums/album-1", None)])

    def test_playlist_query_options(self):
        client = FakeSpotifyClient()

        playlist = client.playlist(
            "playlist-1",
            market="US",
            fields="id,name",
            additional_types="track,episode",
        )

        self.assertIsInstance(playlist, Playlist)
        self.assertEqual(
            client.calls,
            [
                (
                    "/playlists/playlist-1",
                    {
                        "market": "US",
                        "fields": "id,name",
                        "additional_types": "track,episode",
                    },
                ),
            ],
        )

    def test_create_and_update_playlist_send_expected_bodies(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)

        playlist = client.create_playlist("user-1", "Created Playlist", public=False, description="hello")
        current_user_playlist = client.create_current_user_playlist("Created Playlist", public=False, description="hello")
        updated = client.update_playlist_details("playlist-1", name="Renamed", public=True)

        self.assertIsInstance(playlist, Playlist)
        self.assertEqual(playlist.name, "Created Playlist")
        self.assertIsInstance(current_user_playlist, Playlist)
        self.assertEqual(current_user_playlist.name, "Created Playlist")
        self.assertIsNone(updated)
        self.assertEqual(
            transport.calls,
            [
                (
                    "POST",
                    "https://api.spotify.com/v1/users/user-1/playlists",
                    '{"name": "Created Playlist", "public": false, "description": "hello"}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "POST",
                    "https://api.spotify.com/v1/me/playlists",
                    '{"name": "Created Playlist", "public": false, "description": "hello"}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/playlists/playlist-1",
                    '{"name": "Renamed", "public": true}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
            ],
        )

    def test_tracks_returns_track_objects(self):
        client = FakeSpotifyClient()

        tracks = client.tracks(["track-1", "track-2"], market="US")

        self.assertEqual([track.name for track in tracks], ["First Track", "Second Track"])
        self.assertEqual(client.calls, [("/tracks", {"market": "US", "ids": "track-1,track-2"})])

    def test_album_tracks_returns_track_page(self):
        client = FakeSpotifyClient()

        page = client.album_tracks("album-1", market="US", limit=1, offset=0)

        self.assertIsInstance(page, TrackPage)
        self.assertEqual(page.items[0].name, "Album Track")
        self.assertEqual(
            client.calls,
            [("/albums/album-1/tracks", {"market": "US", "limit": 1, "offset": 0})],
        )

    def test_next_and_previous_page_follow_spotify_page_urls(self):
        client = FakeSpotifyClient()

        first = client.album_tracks("album-1", limit=1, offset=0)
        second = client.next_page(first)
        previous = client.previous_page(second)

        self.assertIsInstance(second, TrackPage)
        self.assertEqual(second.items[0].name, "Next Album Track")
        self.assertIsInstance(previous, TrackPage)
        self.assertEqual(previous.items[0].name, "Previous Album Track")
        self.assertEqual(
            client.calls,
            [
                ("/albums/album-1/tracks", {"limit": 1, "offset": 0}),
                ("https://api.spotify.com/v1/albums/album-1/tracks?offset=1&limit=1", None),
                ("https://api.spotify.com/v1/albums/album-1/tracks?offset=0&limit=1", None),
            ],
        )

    def test_next_page_returns_none_without_next_url(self):
        client = FakeSpotifyClient()

        page = TrackPage({"items": [], "next": None})

        self.assertIsNone(client.next_page(page))
        self.assertEqual(client.calls, [])

    def test_playlist_items_returns_playlist_track_page(self):
        client = FakeSpotifyClient()

        page = client.playlist_items(
            "playlist-1",
            market="US",
            fields="items(item(name))",
            limit=1,
            additional_types="track,episode",
        )

        self.assertIsInstance(page, PlaylistTrackPage)
        self.assertEqual(page.items[0].item.name, "Playlist Item")
        self.assertEqual(
            client.calls,
            [
                (
                    "/playlists/playlist-1/items",
                    {
                        "market": "US",
                        "limit": 1,
                        "fields": "items(item(name))",
                        "additional_types": "track,episode",
                    },
                ),
            ],
        )

    def test_playlist_tracks_returns_playlist_track_page(self):
        client = FakeSpotifyClient()

        page = client.playlist_tracks("playlist-1", market="US", limit=1)

        self.assertIsInstance(page, PlaylistTrackPage)
        self.assertEqual(page.items[0].item.name, "Playlist Track")
        self.assertEqual(client.calls, [("/playlists/playlist-1/tracks", {"market": "US", "limit": 1})])

    def test_add_and_remove_playlist_items_send_expected_bodies(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)

        added = client.add_playlist_items("playlist-1", ["spotify:track:1", "spotify:track:2"], position=3)
        removed = client.remove_playlist_items("playlist-1", "spotify:track:1", snapshot_id="snapshot-0")
        reordered = client.reorder_playlist_items("playlist-1", 1, 3, range_length=2, snapshot_id="snapshot-1")
        replaced = client.replace_playlist_items("playlist-1", ["spotify:track:3"])

        self.assertIsInstance(added, SnapshotResult)
        self.assertEqual(added.snapshot_id, "snapshot-1")
        self.assertEqual(removed.snapshot_id, "snapshot-1")
        self.assertEqual(reordered.snapshot_id, "snapshot-2")
        self.assertEqual(replaced.snapshot_id, "snapshot-2")
        self.assertEqual(
            transport.calls,
            [
                (
                    "POST",
                    "https://api.spotify.com/v1/playlists/playlist-1/items",
                    '{"uris": ["spotify:track:1", "spotify:track:2"], "position": 3}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "DELETE",
                    "https://api.spotify.com/v1/playlists/playlist-1/items",
                    '{"items": [{"uri": "spotify:track:1"}], "snapshot_id": "snapshot-0"}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/playlists/playlist-1/items",
                    '{"range_start": 1, "insert_before": 3, "range_length": 2, "snapshot_id": "snapshot-1"}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/playlists/playlist-1/items",
                    '{"uris": ["spotify:track:3"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
            ],
        )

    def test_add_and_remove_playlist_tracks_send_expected_bodies(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)

        added = client.add_playlist_tracks("playlist-1", ["spotify:track:1"], position=3)
        removed = client.remove_playlist_tracks("playlist-1", "spotify:track:1", snapshot_id="snapshot-0")
        reordered = client.reorder_playlist_tracks("playlist-1", 1, 3, range_length=2, snapshot_id="snapshot-1")
        replaced = client.replace_playlist_tracks("playlist-1", ["spotify:track:3"])

        self.assertIsInstance(added, SnapshotResult)
        self.assertEqual(added.snapshot_id, "snapshot-1")
        self.assertEqual(removed.snapshot_id, "snapshot-1")
        self.assertEqual(reordered.snapshot_id, "snapshot-2")
        self.assertEqual(replaced.snapshot_id, "snapshot-2")
        self.assertEqual(
            transport.calls,
            [
                (
                    "POST",
                    "https://api.spotify.com/v1/playlists/playlist-1/tracks",
                    '{"uris": ["spotify:track:1"], "position": 3}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "DELETE",
                    "https://api.spotify.com/v1/playlists/playlist-1/tracks",
                    '{"tracks": [{"uri": "spotify:track:1"}], "snapshot_id": "snapshot-0"}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/playlists/playlist-1/tracks",
                    '{"range_start": 1, "insert_before": 3, "range_length": 2, "snapshot_id": "snapshot-1"}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/playlists/playlist-1/tracks",
                    '{"uris": ["spotify:track:3"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
            ],
        )

    def test_playlist_item_methods_accept_objects_with_uri(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)
        track = Track({"id": "track-1", "uri": "spotify:track:1"})

        client.add_playlist_items("playlist-1", [track])
        client.replace_playlist_items("playlist-1", [track])

        self.assertEqual(
            transport.calls,
            [
                (
                    "POST",
                    "https://api.spotify.com/v1/playlists/playlist-1/items",
                    '{"uris": ["spotify:track:1"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/playlists/playlist-1/items",
                    '{"uris": ["spotify:track:1"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
            ],
        )

    def test_playlist_follow_methods_send_expected_requests(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)

        client.follow_playlist("playlist-1", public=False)
        client.unfollow_playlist("playlist-1")

        self.assertEqual(
            transport.calls,
            [
                (
                    "PUT",
                    "https://api.spotify.com/v1/playlists/playlist-1/followers",
                    '{"public": false}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "DELETE",
                    "https://api.spotify.com/v1/playlists/playlist-1/followers",
                    None,
                    {"Authorization": "Bearer token"},
                ),
            ],
        )

    def test_playlist_followers_contains_returns_boolean_tuple(self):
        client = FakeSpotifyClient()

        follows = client.playlist_followers_contains("playlist-1", ["user-1", "user-2"])

        self.assertEqual(follows, (True, False))
        self.assertEqual(
            client.calls,
            [("/playlists/playlist-1/followers/contains", {"ids": "user-1,user-2"})],
        )

    def test_artist_top_tracks_returns_track_objects(self):
        client = FakeSpotifyClient()

        tracks = client.artist_top_tracks("artist-1", market="US")

        self.assertEqual(tracks[0].name, "Artist Top Track")
        self.assertEqual(client.calls, [("/artists/artist-1/top-tracks", {"market": "US"})])

    def test_artist_related_artists_returns_artist_objects(self):
        client = FakeSpotifyClient()

        artists = client.artist_related_artists("artist-1")

        self.assertEqual(artists[0].name, "Related Artist")
        self.assertEqual(client.calls, [("/artists/artist-1/related-artists", None)])

    def test_lazy_hydration_uses_current_client(self):
        client = FakeSpotifyClient()
        track = Track({"id": "track-1", "name": "Simplified Track"})

        self.assertEqual(track.album.name, "Fetched Album")
        self.assertEqual(client.calls, [("/tracks/track-1", None)])

    def test_audio_features_returns_audio_features_object(self):
        client = FakeSpotifyClient()

        features = client.audio_features("track-1")

        self.assertEqual(features.danceability, 0.8)
        self.assertEqual(client.calls, [("/audio-features/track-1", None)])

    def test_recommendations_returns_recommendations_object(self):
        client = FakeSpotifyClient()

        recommendations = client.recommendations(
            seed_artists=["artist-1"],
            seed_tracks="track-1",
            limit=1,
            min_energy=0.5,
        )

        self.assertIsInstance(recommendations, Recommendations)
        self.assertEqual(recommendations.tracks[0].name, "Recommended Track")
        self.assertEqual(
            client.calls,
            [
                (
                    "/recommendations",
                    {
                        "seed_artists": "artist-1",
                        "seed_tracks": "track-1",
                        "limit": 1,
                        "min_energy": 0.5,
                    },
                ),
            ],
        )

    def test_categories_unwraps_categories_page(self):
        client = FakeSpotifyClient()

        categories = client.categories(country="US", limit=1)

        self.assertIsInstance(categories, CategoryPage)
        self.assertEqual(categories.items[0].name, "Pop")
        self.assertEqual(client.calls, [("/browse/categories", {"limit": 1, "country": "US"})])

    def test_category_playlists_unwraps_playlist_page(self):
        client = FakeSpotifyClient()

        playlists = client.category_playlists("pop", limit=1)

        self.assertIsInstance(playlists, PlaylistPage)
        self.assertEqual(playlists.items[0].name, "Category Playlist")
        self.assertEqual(client.calls, [("/browse/categories/pop/playlists", {"limit": 1})])

    def test_new_releases_unwraps_album_page(self):
        client = FakeSpotifyClient()

        albums = client.new_releases(country="US", limit=1)

        self.assertIsInstance(albums, AlbumPage)
        self.assertEqual(albums.items[0].name, "New Album")
        self.assertEqual(client.calls, [("/browse/new-releases", {"limit": 1, "country": "US"})])

    def test_search_returns_search_results(self):
        client = FakeSpotifyClient()

        results = client.search("hello", ["track", "artist"], market="US", limit=1)

        self.assertIsInstance(results, SearchResults)
        self.assertEqual(results.tracks.items[0].name, "Search Track")
        self.assertEqual(results.artists.items[0].name, "Search Artist")
        self.assertEqual(
            client.calls,
            [("/search", {"market": "US", "limit": 1, "q": "hello", "type": "track,artist"})],
        )

    def test_current_playback_returns_currently_playing_object(self):
        client = FakeSpotifyClient()

        current = client.current_playback(market="US", additional_types="track,episode")

        self.assertIsInstance(current, CurrentlyPlaying)
        self.assertEqual(current.item.name, "Current Track")
        self.assertEqual(
            client.calls,
            [("/me/player", {"market": "US", "additional_types": "track,episode"})],
        )

    def test_devices_returns_device_objects(self):
        client = FakeSpotifyClient()

        devices = client.devices()

        self.assertIsInstance(devices[0], Device)
        self.assertEqual(devices[0].name, "Desktop")
        self.assertEqual(client.calls, [("/me/player/devices", None)])

    def test_recently_played_returns_play_history_cursor_page(self):
        client = FakeSpotifyClient()

        page = client.recently_played(limit=1, after="after-0")

        self.assertIsInstance(page, PlayHistoryCursorPage)
        self.assertEqual(page.items[0].track.name, "Recent Track")
        self.assertEqual(page.cursors.after, "after-1")
        self.assertEqual(
            client.calls,
            [("/me/player/recently-played", {"limit": 1, "after": "after-0"})],
        )

    def test_current_user_playlists_returns_playlist_page(self):
        client = FakeSpotifyClient()

        page = client.current_user_playlists(limit=1, offset=0)

        self.assertIsInstance(page, PlaylistPage)
        self.assertEqual(page.items[0].name, "Current User Playlist")
        self.assertEqual(client.calls, [("/me/playlists", {"limit": 1, "offset": 0})])

    def test_user_playlists_returns_playlist_page(self):
        client = FakeSpotifyClient()

        page = client.user_playlists("user-1", limit=1)

        self.assertIsInstance(page, PlaylistPage)
        self.assertEqual(page.items[0].name, "Public User Playlist")
        self.assertEqual(client.calls, [("/users/user-1/playlists", {"limit": 1})])

    def test_saved_library_pages_return_wrapped_items(self):
        client = FakeSpotifyClient()

        albums = client.saved_albums(market="US", limit=1)
        tracks = client.saved_tracks(market="US", limit=1)
        episodes = client.saved_episodes(market="US", limit=1)
        shows = client.saved_shows(limit=1)

        self.assertIsInstance(albums, SavedAlbumPage)
        self.assertEqual(albums.items[0].album.name, "Saved Album")
        self.assertIsInstance(tracks, SavedTrackPage)
        self.assertEqual(tracks.items[0].track.name, "Saved Track")
        self.assertIsInstance(episodes, SavedEpisodePage)
        self.assertEqual(episodes.items[0].episode.name, "Saved Episode")
        self.assertIsInstance(shows, SavedShowPage)
        self.assertEqual(shows.items[0].show.name, "Saved Show")
        self.assertEqual(
            client.calls,
            [
                ("/me/albums", {"market": "US", "limit": 1}),
                ("/me/tracks", {"market": "US", "limit": 1}),
                ("/me/episodes", {"market": "US", "limit": 1}),
                ("/me/shows", {"limit": 1}),
            ],
        )

    def test_contains_saved_methods_return_boolean_tuples(self):
        client = FakeSpotifyClient()

        self.assertEqual(client.contains_saved_albums(["album-1", "album-2"]), (True, False))
        self.assertEqual(client.contains_saved_tracks(["track-1", "track-2"]), (True, False))
        self.assertEqual(client.contains_saved_episodes(["episode-1", "episode-2"]), (True, False))
        self.assertEqual(client.contains_saved_shows(["show-1", "show-2"]), (True, False))
        self.assertEqual(client.contains_saved_audiobooks(["audiobook-1", "audiobook-2"]), (True, False))
        self.assertEqual(
            client.calls,
            [
                ("/me/albums/contains", {"ids": "album-1,album-2"}),
                ("/me/tracks/contains", {"ids": "track-1,track-2"}),
                ("/me/episodes/contains", {"ids": "episode-1,episode-2"}),
                ("/me/shows/contains", {"ids": "show-1,show-2"}),
                ("/me/audiobooks/contains", {"ids": "audiobook-1,audiobook-2"}),
            ],
        )

    def test_save_and_remove_library_methods_send_json_bodies(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)

        self.assertIsNone(client.save_tracks(["track-1", "track-2"]))
        self.assertIsNone(client.remove_saved_tracks("track-1"))

        self.assertEqual(
            transport.calls,
            [
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/tracks",
                    '{"ids": ["track-1", "track-2"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "DELETE",
                    "https://api.spotify.com/v1/me/tracks",
                    '{"ids": ["track-1"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
            ],
        )

    def test_generic_library_methods_use_uri_query(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)
        track = Track({"id": "track-1", "uri": "spotify:track:1"})

        self.assertIsNone(client.save_library_items([track, "spotify:album:1"]))
        self.assertIsNone(client.remove_library_items("spotify:track:1"))

        self.assertEqual(
            transport.calls,
            [
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/library?uris=spotify%3Atrack%3A1%2Cspotify%3Aalbum%3A1",
                    None,
                    {"Authorization": "Bearer token"},
                ),
                (
                    "DELETE",
                    "https://api.spotify.com/v1/me/library?uris=spotify%3Atrack%3A1",
                    None,
                    {"Authorization": "Bearer token"},
                ),
            ],
        )

    def test_library_contains_returns_boolean_tuple(self):
        client = FakeSpotifyClient()
        track = Track({"id": "track-1", "uri": "spotify:track:1"})

        contains = client.library_contains([track, "spotify:album:1"])

        self.assertEqual(contains, (True, False))
        self.assertEqual(
            client.calls,
            [("/me/library/contains", {"uris": "spotify:track:1,spotify:album:1"})],
        )

    def test_id_methods_accept_objects_with_id(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)
        track = Track({"id": "track-1", "uri": "spotify:track:1"})

        client.save_tracks([track])

        self.assertEqual(
            transport.calls,
            [
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/tracks",
                    '{"ids": ["track-1"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
            ],
        )

    def test_playback_write_methods_send_expected_requests(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)

        client.transfer_playback(["device-1"], play=True)
        client.play(device_id="device-1", uris=["spotify:track:1"], position_ms=1000)
        client.pause(device_id="device-1")
        client.next_track()
        client.seek(5000, device_id="device-1")
        client.repeat("track", device_id="device-1")
        client.shuffle(False, device_id="device-1")
        client.volume(50, device_id="device-1")
        client.add_to_queue("spotify:track:2", device_id="device-1")

        self.assertEqual(
            transport.calls,
            [
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/player",
                    '{"device_ids": ["device-1"], "play": true}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/player/play?device_id=device-1",
                    '{"uris": ["spotify:track:1"], "position_ms": 1000}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/player/pause?device_id=device-1",
                    None,
                    {"Authorization": "Bearer token"},
                ),
                (
                    "POST",
                    "https://api.spotify.com/v1/me/player/next",
                    None,
                    {"Authorization": "Bearer token"},
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/player/seek?position_ms=5000&device_id=device-1",
                    None,
                    {"Authorization": "Bearer token"},
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/player/repeat?state=track&device_id=device-1",
                    None,
                    {"Authorization": "Bearer token"},
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/player/shuffle?state=false&device_id=device-1",
                    None,
                    {"Authorization": "Bearer token"},
                ),
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/player/volume?volume_percent=50&device_id=device-1",
                    None,
                    {"Authorization": "Bearer token"},
                ),
                (
                    "POST",
                    "https://api.spotify.com/v1/me/player/queue?uri=spotify%3Atrack%3A2&device_id=device-1",
                    None,
                    {"Authorization": "Bearer token"},
                ),
            ],
        )

    def test_playback_uri_methods_accept_objects_with_uri(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)
        track = Track({"id": "track-1", "uri": "spotify:track:1"})

        client.play(uris=[track])
        client.add_to_queue(track)

        self.assertEqual(
            transport.calls,
            [
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/player/play",
                    '{"uris": ["spotify:track:1"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "POST",
                    "https://api.spotify.com/v1/me/player/queue?uri=spotify%3Atrack%3A1",
                    None,
                    {"Authorization": "Bearer token"},
                ),
            ],
        )

    def test_followed_and_top_pages_return_expected_page_types(self):
        client = FakeSpotifyClient()

        followed = client.followed_artists(after="artist-0", limit=1)
        top_artists = client.top_artists(time_range="short_term", limit=1)
        top_tracks = client.top_tracks(time_range="short_term", limit=1)

        self.assertIsInstance(followed, ArtistCursorPage)
        self.assertEqual(followed.items[0].name, "Followed Artist")
        self.assertEqual(followed.cursors.after, "artist-1")
        self.assertIsInstance(top_artists, ArtistPage)
        self.assertEqual(top_artists.items[0].name, "Top Artist")
        self.assertIsInstance(top_tracks, TrackPage)
        self.assertEqual(top_tracks.items[0].name, "Top Track")
        self.assertEqual(
            client.calls,
            [
                ("/me/following", {"type": "artist", "after": "artist-0", "limit": 1}),
                ("/me/top/artists", {"limit": 1, "time_range": "short_term"}),
                ("/me/top/tracks", {"limit": 1, "time_range": "short_term"}),
            ],
        )

    def test_following_contains_methods_return_boolean_tuples(self):
        client = FakeSpotifyClient()

        self.assertEqual(client.follows_artists(["artist-1", "artist-2"]), (True, False))
        self.assertEqual(client.follows_users(["user-1", "user-2"]), (True, False))
        self.assertEqual(
            client.calls,
            [
                ("/me/following/contains", {"type": "artist", "ids": "artist-1,artist-2"}),
                ("/me/following/contains", {"type": "user", "ids": "user-1,user-2"}),
            ],
        )

    def test_follow_and_unfollow_methods_send_type_query_and_json_body(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)

        self.assertIsNone(client.follow_artists(["artist-1"]))
        self.assertIsNone(client.unfollow_users(["user-1", "user-2"]))

        self.assertEqual(
            transport.calls,
            [
                (
                    "PUT",
                    "https://api.spotify.com/v1/me/following?type=artist",
                    '{"ids": ["artist-1"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
                (
                    "DELETE",
                    "https://api.spotify.com/v1/me/following?type=user",
                    '{"ids": ["user-1", "user-2"]}',
                    {
                        "Authorization": "Bearer token",
                        "Content-Type": "application/json",
                    },
                ),
            ],
        )

    def test_playlist_cover_image_returns_images(self):
        client = FakeSpotifyClient()

        images = client.playlist_cover_image("playlist-1")

        self.assertIsInstance(images[0], Image)
        self.assertEqual(images[0].url, "https://example.com/cover.jpg")
        self.assertEqual(client.calls, [("/playlists/playlist-1/images", None)])

    def test_set_playlist_cover_image_sends_raw_jpeg_body(self):
        transport = FakeWriteTransport()
        client = SpotifyClient(access_token="token", transport=transport, auto_set=False)

        self.assertIsNone(client.set_playlist_cover_image("playlist-1", "base64jpeg"))

        self.assertEqual(
            transport.calls,
            [
                (
                    "PUT",
                    "https://api.spotify.com/v1/playlists/playlist-1/images",
                    "base64jpeg",
                    {
                        "Content-Type": "image/jpeg",
                        "Authorization": "Bearer token",
                    },
                ),
            ],
        )

    def test_markets_and_recommendation_genres_return_plain_values(self):
        client = FakeSpotifyClient()

        markets = client.available_markets()
        genres = client.recommendation_genres()

        self.assertEqual(markets, ["US", "GB"])
        self.assertEqual(genres, ["pop", "rock"])
        self.assertEqual(
            client.calls,
            [
                ("/markets", None),
                ("/recommendations/available-genre-seeds", None),
            ],
        )

    def test_get_json_requires_access_token(self):
        client = SpotifyClient(auto_set=False)

        with self.assertRaises(SpotifyClientError):
            client._get_json("/tracks/track-1")

    def test_get_json_uses_transport_with_bearer_token(self):
        calls = []

        def transport(url, headers):
            calls.append((url, headers))
            return {"id": "track-1", "name": "Transport Track"}

        client = SpotifyClient(access_token="abc123", transport=transport, auto_set=False)

        data = client._get_json("/tracks/track-1", query={"market": "US"})

        self.assertEqual(data["name"], "Transport Track")
        self.assertEqual(
            calls,
            [
                (
                    "https://api.spotify.com/v1/tracks/track-1?market=US",
                    {"Authorization": "Bearer abc123"},
                ),
            ],
        )

    def test_url_encodes_query_values(self):
        client = SpotifyClient(access_token="abc123", auto_set=False)

        self.assertEqual(
            client._url("/playlists/playlist-1", {"fields": "id,name", "market": "US"}),
            "https://api.spotify.com/v1/playlists/playlist-1?fields=id%2Cname&market=US",
        )


if __name__ == "__main__":
    unittest.main()
