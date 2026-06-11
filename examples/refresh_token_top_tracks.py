from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client


def main():
    client = user_client()
    page = client.top_tracks(limit=5)

    for track in page:
        print("-", track.name)


if __name__ == "__main__":
    main()
