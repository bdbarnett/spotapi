# MicroPython cannot import names re-exported from spotapi/__init__.py; use submodules.
import os

from spotapi.auth import (
    AuthorizationCodeAuth,
    TokenCache,
    credentials_from_config,
    load_config,
    redirect_uri_from_config,
    PLAYBACK_READ_SCOPES,
    PLAYBACK_WRITE_SCOPES,
    PLAYLIST_READ_SCOPES,
    USER_PROFILE_SCOPES,
)
from spotapi.client import SpotifyClient

SCOPES = (
    USER_PROFILE_SCOPES
    + PLAYBACK_READ_SCOPES
    + PLAYBACK_WRITE_SCOPES
    + PLAYLIST_READ_SCOPES
)


def _app_dir():
    try:
        path = __file__
        if "/" in path:
            return path.rsplit("/", 1)[0]
    except NameError:
        pass
    return os.getcwd()


def _join_dir(directory, name):
    if directory.endswith("/"):
        return directory + name
    return directory + "/" + name


CONFIG_PATH = _join_dir(_app_dir(), "spotapi.local.json")
TOKEN_PATH = _join_dir(_app_dir(), "tokens.json")


class SpotifyController:
    def __init__(self):
        config = load_config(CONFIG_PATH)
        client_id, client_secret = credentials_from_config(config)
        cache = TokenCache(TOKEN_PATH)
        auth = AuthorizationCodeAuth(
            client_id,
            client_secret,
            redirect_uri_from_config(config),
            scope=SCOPES,
            token_cache=cache,
        )
        cache.load_auth(auth)
        self.client = SpotifyClient(auth=auth)
        self._me = None
        self._playlists = None

    def me(self):
        if self._me is None:
            self._me = self.client.me()
        return self._me

    def refresh_now_playing(self):
        current = self.client.current_playback()
        if current is None or not current.raw():
            return {
                "playing": False,
                "track": "",
                "artist": "",
                "progress_ms": 0,
                "duration_ms": 0,
                "device": "",
            }

        item = current.item
        track = ""
        artist = ""
        duration_ms = 0
        if item is not None:
            track = item.name or ""
            duration_ms = getattr(item, "duration_ms", 0) or 0
            artists = getattr(item, "artists", None)
            if artists:
                artist = artists[0].name or ""

        device = ""
        if current.device is not None:
            device = current.device.name or ""

        return {
            "playing": bool(current.is_playing),
            "track": track,
            "artist": artist,
            "progress_ms": current.progress_ms or 0,
            "duration_ms": duration_ms,
            "device": device,
        }

    def play_pause(self):
        state = self.refresh_now_playing()
        if state["playing"]:
            self.client.pause()
        else:
            self.client.play()

    def next_track(self):
        self.client.next_track()

    def previous_track(self):
        self.client.previous_track()

    def owned_playlists(self):
        if self._playlists is not None:
            return self._playlists

        me = self.me()
        playlists = []
        for playlist in self.client.current_user_playlists():
            if playlist.owner and playlist.owner.id == me.id:
                playlists.append({"name": playlist.name, "uri": playlist.uri})
        self._playlists = playlists
        return playlists

    def play_context(self, context_uri):
        self.client.play(context_uri=context_uri)
