import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from spotapi import SpotifyClient


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")

    client = SpotifyClient(client_id=client_id, client_secret=client_secret)
    track = client.track("11dFghVXANMlKmJXsNCbNl", market="US")

    print("track:", track.name)
    print("album:", track.album.name)
    print("artist:", track.artists[0].name)


if __name__ == "__main__":
    main()
