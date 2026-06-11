from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client


def main():
    client = user_client()
    page = client.current_user_playlists(limit=10)

    for playlist in page:
        print("-", playlist.name, "tracks:", playlist.tracks.total)


if __name__ == "__main__":
    main()
