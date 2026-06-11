import inspect

from _bootstrap import bootstrap

bootstrap()

from spotapi import SpotifyClient


NO_ARG_READ_METHODS = (
    "me",
    "queue",
    "devices",
    "available_markets",
    "recommendation_genres",
    "current_playback",
    "currently_playing",
    "recently_played",
    "current_user_playlists",
    "saved_albums",
    "saved_tracks",
    "saved_episodes",
    "saved_shows",
    "saved_audiobooks",
    "followed_artists",
    "top_artists",
    "top_tracks",
    "categories",
    "featured_playlists",
    "new_releases",
)


def callable_without_args(method):
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return False

    for parameter in signature.parameters.values():
        if parameter.name == "self":
            continue
        if parameter.default is inspect.Parameter.empty:
            return False
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            return False

    return True


def main():
    client = SpotifyClient()

    for name in NO_ARG_READ_METHODS:
        method = getattr(client, name)
        if not callable_without_args(method):
            raise SystemExit("Expected {}() to accept no arguments".format(name))

        label = "client.{}()".format(name)
        try:
            print(label, method())
        except Exception as error:
            print(label, "ERROR:", error)


if __name__ == "__main__":
    main()
