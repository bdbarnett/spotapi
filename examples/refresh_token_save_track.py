import os

from _local_oauth import refresh_token_client


TRACK_ID = "11dFghVXANMlKmJXsNCbNl"


def main():
    if os.environ.get("SPOTIFY_RUN_WRITE_EXAMPLE") != "1":
        raise SystemExit("Set SPOTIFY_RUN_WRITE_EXAMPLE=1 to save a track to your library")

    client = refresh_token_client()
    client.save_tracks([TRACK_ID])

    saved = client.contains_saved_tracks([TRACK_ID])
    print("saved:", saved[0])


if __name__ == "__main__":
    main()
