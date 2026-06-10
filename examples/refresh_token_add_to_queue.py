import os

from _local_oauth import refresh_token_client


TRACK_URI = "spotify:track:11dFghVXANMlKmJXsNCbNl"


def main():
    if os.environ.get("SPOTIFY_RUN_WRITE_EXAMPLE") != "1":
        raise SystemExit("Set SPOTIFY_RUN_WRITE_EXAMPLE=1 to add a track to your queue")

    uri = os.environ.get("SPOTIFY_TRACK_URI", TRACK_URI)

    client = refresh_token_client()
    client.add_to_queue(uri)

    print("queued:", uri)


if __name__ == "__main__":
    main()
