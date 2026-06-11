from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client


def main():
    client = user_client()
    page = client.top_artists(limit=5)

    for artist in page:
        print("-", artist.name)


if __name__ == "__main__":
    main()
