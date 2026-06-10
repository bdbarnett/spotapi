import os

from _local_oauth import refresh_token_client
from spotapi import snapshot_id


TRACK_URI = "spotify:track:11dFghVXANMlKmJXsNCbNl"


def main():
    if os.environ.get("SPOTIFY_RUN_WRITE_EXAMPLE") != "1":
        raise SystemExit("Set SPOTIFY_RUN_WRITE_EXAMPLE=1 to add a track to a playlist")

    playlist_id = os.environ.get("SPOTIFY_PLAYLIST_ID")
    if not playlist_id:
        raise SystemExit("Set SPOTIFY_PLAYLIST_ID")

    client = refresh_token_client()
    result = client.add_playlist_items(playlist_id, [TRACK_URI])

    print("snapshot_id:", snapshot_id(result))


if __name__ == "__main__":
    main()
