from _local_oauth import refresh_token_client


def main():
    client = refresh_token_client()
    page = client.recently_played(limit=10)

    if not page.items:
        print("No recently played tracks.")
        return

    for history in page:
        print(history.played_at, "-", history.track.name)
        artists = history.track.artists
        if artists:
            print("  artists:", ", ".join(artist.name for artist in artists))
        if history.context is not None:
            print("  context:", history.context.type, history.context.uri)


if __name__ == "__main__":
    main()
