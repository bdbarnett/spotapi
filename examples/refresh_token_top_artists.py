from _local_oauth import refresh_token_client


def main():
    client = refresh_token_client()
    page = client.top_artists(time_range="short_term", limit=10)

    if not page.items:
        print("No top artists.")
        return

    for index, artist in enumerate(page, 1):
        print(str(index) + ".", artist.name)
        if artist.genres:
            print("   genres:", ", ".join(artist.genres))
        print("   popularity:", artist.popularity)


if __name__ == "__main__":
    main()
