from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client


def main():
    client = user_client()
    page = client.recently_played(limit=5)

    for item in page:
        track = item.track
        print("-", item.played_at, track.name)


if __name__ == "__main__":
    main()
