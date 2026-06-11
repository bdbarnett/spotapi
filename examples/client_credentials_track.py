from _bootstrap import bootstrap

bootstrap()

from spotapi import app_client


TRACK_ID = "11dFghVXANMlKmJXsNCbNl"


def main():
    client = app_client()
    track = client.track(TRACK_ID, market="US")

    print("track:", track.name)
    print("album:", track.album.name)
    print("artists:")
    for artist in track.artists:
        print("-", artist.name)


if __name__ == "__main__":
    main()
