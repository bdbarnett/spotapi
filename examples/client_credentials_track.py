import os

from _bootstrap import bootstrap

bootstrap()

from spotapi import SpotifyClient


TRACK_ID = "11dFghVXANMlKmJXsNCbNl"


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")

    client = SpotifyClient(client_id=client_id, client_secret=client_secret)
    track = client.track(TRACK_ID, market="US")

    print("track:", track.name)
    print("album:", track.album.name)
    print("artists:")
    for artist in track.artists:
        print("-", artist.name)


if __name__ == "__main__":
    main()
