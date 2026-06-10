import os

from _bootstrap import bootstrap

bootstrap()

from spotapi import SpotifyClient


ALBUM_ID = "4aawyAB9vmqN3uQ7FjRGTy"


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")

    client = SpotifyClient(client_id=client_id, client_secret=client_secret)
    page = client.album_tracks(ALBUM_ID, market="US", limit=2)

    print("first page:")
    print_tracks(page)

    next_page = client.next_page(page)
    if next_page is not None:
        print("next page:")
        print_tracks(next_page)


def print_tracks(page):
    for track in page:
        print("-", track.track_number, track.name)


if __name__ == "__main__":
    main()
