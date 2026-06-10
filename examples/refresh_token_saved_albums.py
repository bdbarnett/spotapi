from _local_oauth import refresh_token_client


def main():
    client = refresh_token_client()
    page = client.saved_albums(market="US", limit=10)

    if not page.items:
        print("No saved albums.")
        return

    for saved_album in page:
        album = saved_album.album
        print(saved_album.added_at, "-", album.name)
        if album.artists:
            print("  artists:", ", ".join(artist.name for artist in album.artists))
        print("  total_tracks:", album.total_tracks)


if __name__ == "__main__":
    main()
