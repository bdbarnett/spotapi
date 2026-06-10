from _local_oauth import refresh_token_client


def main():
    client = refresh_token_client()
    page = client.current_user_playlists(limit=10)

    for playlist in page:
        print("-", playlist.name, "tracks:", playlist.tracks.total)


if __name__ == "__main__":
    main()
