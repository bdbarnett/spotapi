from _local_oauth import refresh_token_client


def main():
    client = refresh_token_client()
    page = client.top_tracks(time_range="short_term", limit=10)

    if not page.items:
        print("No top tracks.")
        return

    for index, track in enumerate(page, 1):
        print(str(index) + ".", track.name)
        if track.artists:
            print("   artists:", ", ".join(artist.name for artist in track.artists))
        if track.album is not None:
            print("   album:", track.album.name)


if __name__ == "__main__":
    main()
