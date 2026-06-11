from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client


def main():
    client = user_client()
    page = client.saved_albums(limit=5)

    for saved_album in page:
        album = saved_album.album
        print("-", saved_album.added_at, album.name)


if __name__ == "__main__":
    main()
